"""Matrix expansion + sequential case scheduling into worker subprocesses."""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import platform
import socket
import subprocess
import sys

from benchmark.backends import BACKENDS
from benchmark.presets import PRESETS, SEED, Group
from benchmark.registry import CIRCUITS, NOISE

THREAD_ENV_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def _worker_env(threads: int) -> dict:
    """Environment for a worker subprocess: BLAS/OpenMP thread counts pinned
    to ``threads`` *before* any simulator import, plus quiet defaults."""
    env = dict(os.environ)
    for var in THREAD_ENV_VARS:
        env[var] = str(threads)
    env["QUTIP_NUM_PROCESSES"] = "1"
    env["OMP_PROC_BIND"] = "false"
    return env


def _call_worker(args: list[str], env: dict, timeout: int) -> dict:
    """Run ``python -m benchmark.worker <args>`` and parse its JSON line.

    Returns ``{"status": "timeout" | "error", ...}`` on failure instead of
    raising, so one bad case never aborts the whole matrix.
    """
    cmd = [sys.executable, "-m", "benchmark.worker", *args]
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if proc.returncode != 0:
        return {"status": "error", "error": f"worker exit {proc.returncode}",
                "stderr": proc.stderr[-2000:]}
    line = proc.stdout.strip().splitlines()
    if not line:
        return {"status": "error", "error": "worker produced no output",
                "stderr": proc.stderr[-2000:]}
    try:
        return json.loads(line[-1])
    except json.JSONDecodeError:
        return {"status": "error", "error": "invalid worker JSON",
                "stdout": line[-1][:2000]}


def probe_backends(backend_names: list[str]) -> dict[str, dict]:
    """Import-probe each backend in a subprocess.

    Returns ``{name: {"available", "version", "reason"}}``; the version is
    best-effort (module ``__version__`` or installed distribution metadata).
    """
    info: dict[str, dict] = {}
    for name in backend_names:
        info[name] = _call_worker(["--probe", name], _worker_env(1), timeout=180)
    return info


def selftest_backends(backend_names: list[str]) -> dict[str, dict]:
    """Run the known-answer check (``worker --selftest``) per backend."""
    results: dict[str, dict] = {}
    for name in backend_names:
        results[name] = _call_worker(["--selftest", name], _worker_env(1), timeout=180)
    return results


def expand_groups(groups: list[Group]) -> list[dict]:
    """Expand preset groups into concrete case dicts (no availability filter)."""

    cases: list[dict] = []
    for group in groups:
        for backend in group.backends:
            if backend == "all_sv":
                names = [n for n, cls in BACKENDS.items() if cls.kind == "statevector"]
            elif backend == "all_dm":
                names = [n for n, cls in BACKENDS.items() if cls.kind == "density"]
            else:
                names = [backend]
            for name in sorted(names):
                if name not in BACKENDS:
                    raise ValueError(f"unknown backend {name!r}")
                for circuit in group.circuits:
                    if circuit not in CIRCUITS:
                        raise ValueError(f"unknown circuit family {circuit!r}")
                    if group.noise not in NOISE:
                        raise ValueError(f"unknown noise preset {group.noise!r}")
                    for n_qubits in group.qubits:
                        for threads in group.threads:
                            case = {
                                "group": group.name,
                                "backend": name,
                                "circuit": circuit,
                                "n_qubits": n_qubits,
                                "depth": group.depth,
                                "noise": group.noise,
                                "shots": group.shots,
                                "threads": threads,
                                "repeats": group.repeats,
                                "seed": SEED,
                                "timeout_s": group.timeout_s,
                            }
                            case["id"] = hashlib.sha1(
                                json.dumps(case, sort_keys=True).encode()
                            ).hexdigest()[:12]
                            cases.append(case)
    return cases


def _case_key(case: dict) -> tuple:
    """Identity of a case for ``--resume`` dedup (everything that changes
    what is being measured)."""
    return (
        case["backend"], case["circuit"], case["n_qubits"], case["depth"],
        case["noise"], case["shots"], case["threads"], case["repeats"],
    )


def _stats(times_ms: list[float]) -> dict:
    """median / mean / std / min over the timed repeats, in milliseconds."""
    if not times_ms:
        return {}
    ordered = sorted(times_ms)
    n = len(ordered)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    mean = sum(ordered) / n
    var = sum((t - mean) ** 2 for t in ordered) / n
    return {
        "median_ms": round(median, 3),
        "mean_ms": round(mean, 3),
        "std_ms": round(math.sqrt(var), 3),
        "min_ms": round(ordered[0], 3),
    }


def collect_env_meta(preset_name: str, probes: dict, selftests: dict) -> dict:
    """Snapshot of the run environment (CPU, memory, python, per-backend
    versions and selftest status) stored alongside the results."""
    def _cpu_model() -> str:
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
        return platform.processor() or "unknown"

    mem_gb = "unknown"
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal"):
                    mem_gb = f"{int(line.split()[1]) / 1024 / 1024:.0f} GB"
    except OSError:
        pass

    return {
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "cpu": _cpu_model(),
        "cores": os.cpu_count(),
        "memory": mem_gb,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "preset": preset_name,
        "backends": probes,
        "selftest": selftests,
    }


def run_matrix(
    preset_name: str,
    out_path: str,
    selected_backends: list[str] | None = None,
    limit: int | None = None,
    resume: bool = False,
) -> dict:
    """Execute a preset matrix and persist a results document.

    Flow: probe availability -> selftest every reachable backend (failures
    are excluded) -> expand cases -> run each in a worker subprocess,
    updating ``out_path`` after every case so an interrupted run can be
    resumed with ``resume=True`` (completed cases are reused, failures
    re-run).  Returns the final ``{"meta", "dropped", "results"}`` dict.
    """
    groups = PRESETS[preset_name]
    cases = expand_groups(groups)

    all_names = sorted({c["backend"] for c in cases})
    probes = probe_backends(all_names)
    available = [n for n in all_names if probes.get(n, {}).get("available")]
    if selected_backends:
        available = [n for n in available if n in selected_backends]
    dropped = {n: probes[n].get("reason", "filtered by --backends")
               for n in all_names if n not in available}

    selftests = selftest_backends(available)
    failed_selftest = [n for n, r in selftests.items() if r.get("selftest") != "pass"]

    cases = [c for c in cases if c["backend"] in available]
    if failed_selftest:
        print(f"[runner] WARNING selftest failed (kept out of results): {failed_selftest}")
        cases = [c for c in cases if c["backend"] not in failed_selftest]

    existing: dict[tuple, dict] = {}
    if resume and os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as fh:
            prior = json.load(fh)
        existing = {_case_key(r): r for r in prior.get("results", [])
                    if r.get("status") == "ok"}
        print(f"[runner] resume: reusing {len(existing)} completed cases")

    if limit:
        cases = cases[:limit]

    meta = collect_env_meta(preset_name, probes, selftests)
    results: list[dict] = [r for r in existing.values()]

    seen = {_case_key(r) for r in results}
    total = len(cases)
    for i, case in enumerate(cases, 1):
        key = _case_key(case)
        if key in seen:
            continue
        payload = _call_worker(
            ["--case-json", json.dumps(case)],
            _worker_env(case["threads"]),
            timeout=case["timeout_s"] + 60,
        )
        record = {**case, **{k: v for k, v in payload.items() if k not in case}}
        if payload.get("status") == "ok":
            record["stats"] = _stats(payload.get("run_ms", []))
            seen.add(key)
        results.append(record)
        tag = payload.get("status", "?")
        ms = record.get("stats", {}).get("median_ms", "-")
        print(f"[{i:>4}/{total}] {case['backend']:<12} {case['circuit']:<7} "
              f"n={case['n_qubits']:<3} noise={case['noise']:<7} shots={case['shots']:<5} "
              f"threads={case['threads']:<2} -> {tag} ({ms} ms)", flush=True)

        out_doc = {"meta": meta, "dropped": dropped, "results": results}
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(out_doc, fh, ensure_ascii=False, indent=1)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "dropped": dropped, "results": results},
                  fh, ensure_ascii=False, indent=1)
    print(f"[runner] wrote {len(results)} records -> {out_path}")
    return {"meta": meta, "dropped": dropped, "results": results}
