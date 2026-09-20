"""Single-case worker. Runs in its own process (spawned by the runner) so
that thread-pinning environment variables take effect before any simulator
import, and so a crash/timeout cannot poison the timing of other cases.

Usage:
    python -m benchmark.worker --case-json '{"backend": ...}' [--selftest]
    python -m benchmark.worker --probe aer_sv

Emits exactly one JSON line on stdout.
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time


def _rss_mb() -> float:
    # ru_maxrss is KiB on Linux
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


def _dist_version(dist_name: str) -> str | None:
    """Best-effort distribution version, ignoring stale *.egg-info leftovers.

    The repo root (on sys.path when running ``python -m benchmark``) can hold
    an ``*.egg-info`` from an old local build whose version shadows the
    actually-installed wheel, so prefer distributions that live in
    site-packages.
    """
    import importlib.metadata as md

    versions = []
    for dist in md.distributions():
        name = (dist.metadata.get("Name") or "").replace("_", "-").lower()
        if name != dist_name.replace("_", "-").lower():
            continue
        path = str(getattr(dist, "_path", ""))
        versions.append(("egg-info" in path, path, dist.version))
    if not versions:
        return None
    versions.sort(key=lambda item: item[0])  # non-egg-info first
    return versions[0][2]


def probe(backend_name: str) -> None:
    from benchmark.backends import BACKENDS

    cls = BACKENDS.get(backend_name)
    if cls is None:
        _emit({"backend": backend_name, "available": False, "version": None,
               "reason": "unknown backend name"})
        return
    available, reason = True, ""
    version = None
    try:
        if cls.import_name:
            import importlib

            mod = importlib.import_module(cls.import_name)
            version = str(getattr(mod, "__version__", ""))
        if not version:
            dist = cls.import_name or "uniqc_cpp"
            version = _dist_version(dist) or _dist_version("uniqc-cppsimulator")
    except Exception as exc:  # noqa: BLE001 - probe reports any import failure
        available, reason = False, f"{type(exc).__name__}: {exc}"
    _emit({"backend": backend_name, "available": available, "version": version or None,
           "reason": reason})


def _reference_cases():
    """Known-answer circuits used to validate adapter correctness/endianness.

    Each entry is ``(circuit, expected_p_q0_1, tolerance)``; ``qft3`` is
    included because its amplitudes exercise the full gate set (H, Rz, CX,
    SWAP) and are uniform, so P(q0=1) must be exactly 0.5 regardless of
    endianness mistakes elsewhere.
    """
    from benchmark.circuits import qft
    from benchmark.ir import Circuit, Op

    x0 = Circuit("selftest_x0", 3, (Op("x", (0,)),))
    h0 = Circuit("selftest_h0", 3, (Op("h", (0,)),))
    ghz = Circuit("selftest_ghz", 3, (Op("h", (0,)), Op("cx", (0, 1)), Op("cx", (1, 2))))
    qft3 = qft(3)
    return [
        (x0, 1.0, 1e-6),
        (h0, 0.5, 1e-6),
        (ghz, 0.5, 1e-6),
        (qft3, 0.5, 1e-6),  # |QFT|0..0> has uniform |amp|^2, P(q0=1)=0.5
    ]


def run_selftest(backend_name: str, threads: int = 1) -> None:
    from benchmark.backends import BACKENDS

    cls = BACKENDS[backend_name]
    backend = cls(threads=threads)
    results = []
    ok = True
    for circuit, expected, tol in _reference_cases():
        reason = backend.supports(circuit, shots=0)
        if reason is not None:
            results.append({"circuit": circuit.name, "skipped": reason})
            continue
        try:
            got = backend.run(circuit, shots=0, seed=42)["p_q0_1"]
            passed = abs(got - expected) <= tol
            ok = ok and passed
            results.append({"circuit": circuit.name, "p_q0_1": got,
                            "expected": expected, "passed": passed})
        except Exception as exc:  # noqa: BLE001 - selftest reports failures
            ok = False
            results.append({"circuit": circuit.name, "error": f"{type(exc).__name__}: {exc}"})
    _emit({"backend": backend_name, "selftest": "pass" if ok else "fail",
           "cases": results})


def run_case(case: dict) -> None:
    """Execute one benchmark case and emit its JSON record.

    Builds the circuit from the registry, applies the noise preset, checks
    support, runs one warm-up + ``case["repeats"]`` timed repeats of
    ``backend.run`` (seed varies per repeat), then reports the raw times,
    the readout scalar and peak RSS.  Emits ``{"status": "skip", ...}``
    when the backend cannot run this case.
    """
    from benchmark.backends import BACKENDS
    from benchmark.ir import apply_noise
    from benchmark.registry import CIRCUITS, NOISE

    backend_cls = BACKENDS[case["backend"]]
    circuit = CIRCUITS[case["circuit"]](case["n_qubits"], case["depth"], case["seed"])
    circuit = apply_noise(circuit, NOISE[case["noise"]])
    shots = case["shots"]

    backend = backend_cls(threads=case["threads"])
    reason = backend.supports(circuit, shots)
    if reason is not None:
        _emit({**case, "status": "skip", "reason": reason})
        return

    backend.run(circuit, shots, seed=case["seed"])  # warm-up (JIT, caches)

    times_ms = []
    p_q0_1 = None
    for repeat in range(case["repeats"]):
        t0 = time.perf_counter()
        out = backend.run(circuit, shots, seed=case["seed"] + repeat)
        times_ms.append((time.perf_counter() - t0) * 1e3)
        p_q0_1 = out["p_q0_1"]

    _emit({
        **case,
        "status": "ok",
        "run_ms": [round(t, 3) for t in times_ms],
        "p_q0_1": p_q0_1,
        "rss_mb": round(_rss_mb(), 1),
    })


def main() -> None:
    """Entry point for ``python -m benchmark.worker`` (see module docstring)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-json")
    parser.add_argument("--probe")
    parser.add_argument("--selftest")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    if args.probe:
        probe(args.probe)
    elif args.selftest:
        run_selftest(args.selftest, args.threads)
    elif args.case_json:
        try:
            run_case(json.loads(args.case_json))
        except Exception as exc:  # noqa: BLE001 - worker reports errors as data
            import traceback

            _emit({"status": "error", "error": f"{type(exc).__name__}: {exc}",
                   "traceback": traceback.format_exc(limit=5)})
    else:  # pragma: no cover
        parser.error("need --case-json, --probe or --selftest")


if __name__ == "__main__":
    main()
