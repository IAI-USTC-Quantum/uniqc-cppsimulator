"""Chart rendering from a results JSON (matplotlib only, no pandas).

Each figure is an independent function so new chart types can be added
without touching the dispatcher: implement ``fig_xxx(data, out_dir)`` and
register it in ``PLOTTERS``.
"""

from __future__ import annotations

import os
from collections.abc import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from benchmark.backends import BACKENDS

FigureFunc = Callable[[dict, str], tuple[str, str]]

PLOTTERS: list[FigureFunc] = []


def plotter(func: FigureFunc) -> FigureFunc:
    PLOTTERS.append(func)
    return func


def _ok(results: list[dict]) -> list[dict]:
    """Only successfully measured records."""
    return [r for r in results if r.get("status") == "ok"]


_NON_UNIQC_PALETTE = ("C0", "C1", "C2", "C5", "C6", "C7", "C8", "C9")  # skips C3 red / C4 purple


def _color_map(backends: list[str]) -> dict[str, str]:
    """Assign colors: uniqc backends get dedicated red/purple, others cycle
    the remaining tab10 entries so no line is confused with uniqc."""
    colors = {}
    i = 0
    for backend in sorted(backends):
        if backend == "uniqc_sv":
            colors[backend] = "#d62728"
        elif backend == "uniqc_dm":
            colors[backend] = "#9467bd"
        else:
            colors[backend] = _NON_UNIQC_PALETTE[i % len(_NON_UNIQC_PALETTE)]
            i += 1
    return colors


def _label(backend: str) -> str:
    return BACKENDS[backend].label if backend in BACKENDS else backend


def _save(fig, out_dir: str, name: str) -> tuple[str, str]:
    """Write a figure to ``out_dir/name`` and return (name, path)."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return name, path


def _select(results: list[dict], *, group: str, threads: int | None = None):
    """Filter to one matrix group (and optionally one thread tier)."""
    rows = [r for r in _ok(results) if r.get("group") == group]
    if threads is not None:
        rows = [r for r in rows if r["threads"] == threads]
    return rows


@plotter
def fig_ideal_runtime(data: dict, out_dir: str) -> tuple[str, str]:
    """Runtime vs qubit count for ideal statevector simulation (per circuit)."""
    results = _select(data["results"], group="ideal-sv")
    if not results:
        return "", ""
    circuits = sorted({r["circuit"] for r in results})
    threads_list = sorted({r["threads"] for r in results})
    # Use the single-thread tier: it is the only one where every backend
    # (incl. uniqc_sv, whose parallelism is shot-level) has comparable data.
    threads = threads_list[0]
    rows = [r for r in results if r["threads"] == threads]

    fig, axes = plt.subplots(
        1, len(circuits), figsize=(5.2 * len(circuits), 4.2), squeeze=False
    )
    colors = _color_map(sorted({r["backend"] for r in rows}))
    for ax, circuit in zip(axes[0], circuits):
        sub = [r for r in rows if r["circuit"] == circuit]
        backends = sorted({r["backend"] for r in sub})
        for backend in backends:
            pts = sorted(
                (r["n_qubits"], r["stats"]["median_ms"])
                for r in sub if r["backend"] == backend
            )
            if not pts:
                continue
            xs, ys = zip(*pts)
            ax.plot(xs, ys, marker="o", label=_label(backend), color=colors[backend],
                    linewidth=2.2 if backend.startswith("uniqc") else 1.4,
                    zorder=3 if backend.startswith("uniqc") else 2)
        ax.set_title(f"{circuit} (threads={threads})")
        ax.set_xlabel("qubits")
        ax.set_ylabel("median wall time [ms]")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(10, len(labels)),
               fontsize=8, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Ideal statevector simulation — runtime vs qubits", y=1.02)
    return _save(fig, out_dir, "ideal_runtime_vs_qubits.png")


@plotter
def fig_thread_speedup(data: dict, out_dir: str) -> tuple[str, str]:
    """Single-thread vs multi-thread speedup per backend (largest common size)."""
    results = _select(data["results"], group="ideal-sv")
    if not results:
        return "", ""
    circuits = sorted({r["circuit"] for r in results})
    threads_list = sorted({r["threads"] for r in results})
    if len(threads_list) < 2:
        return "", ""
    t1, tn = threads_list[0], threads_list[-1]

    fig, ax = plt.subplots(figsize=(1.9 * len(circuits) + 2, 4.6))
    width = 0.8 / len(circuits)
    backends = sorted({r["backend"] for r in results})
    for ci, circuit in enumerate(circuits):
        for bi, backend in enumerate(backends):
            base = [r for r in results if r["circuit"] == circuit
                    and r["backend"] == backend and r["threads"] == t1]
            par = [r for r in results if r["circuit"] == circuit
                   and r["backend"] == backend and r["threads"] == tn]
            if not base or not par:
                continue
            n = max({r["n_qubits"] for r in base} & {r["n_qubits"] for r in par})
            b = next(r for r in base if r["n_qubits"] == n)
            p = next(r for r in par if r["n_qubits"] == n)
            speedup = b["stats"]["median_ms"] / p["stats"]["median_ms"]
            ax.bar(bi + (ci - len(circuits) / 2 + 0.5) * width, speedup,
                   width=width * 0.92, label=f"{circuit} n={n}" if bi == 0 else None,
                   color=f"C{ci}")
    ax.axhline(1.0, color="k", linestyle="--", linewidth=0.8)
    ax.set_xticks(range(len(backends)))
    ax.set_xticklabels([_label(b) for b in backends], rotation=38, ha="right", fontsize=8)
    ax.set_ylabel(f"speedup  (threads=1 time / threads={tn} time)")
    ax.set_title(
        "Single- vs multi-thread baseline (kernel-internal parallelism, largest common n)\n"
        "(uniqc_sv parallelism is shot-level: see sampling_throughput.png)"
    )
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    return _save(fig, out_dir, "thread_speedup.png")


@plotter
def fig_noise_runtime(data: dict, out_dir: str) -> tuple[str, str]:
    """Noise (density-matrix) runtime vs qubits per noise preset."""
    rows = [r for r in _ok(data["results"])
            if str(r.get("group", "")).startswith("noise-dm")]
    if not rows:
        return "", ""
    noise_names = sorted({r["noise"] for r in rows})
    noise_names = [n for n in noise_names if n != "none"] or noise_names
    threads = min(r["threads"] for r in rows)

    fig, axes = plt.subplots(
        1, len(noise_names), figsize=(5.0 * len(noise_names), 4.2), squeeze=False
    )
    colors = _color_map(sorted({r["backend"] for r in rows}))
    for ax, noise in zip(axes[0], noise_names):
        sub = [r for r in rows if r["noise"] == noise and r["threads"] == threads]
        backends = sorted({r["backend"] for r in sub})
        for backend in backends:
            pts = sorted(
                (r["n_qubits"], r["stats"]["median_ms"])
                for r in sub if r["backend"] == backend
            )
            if not pts:
                continue
            xs, ys = zip(*pts)
            ax.plot(xs, ys, marker="s", label=_label(backend), color=colors[backend],
                    linewidth=2.2 if backend.startswith("uniqc") else 1.4)
        ax.set_title(f"noise: {noise} (threads={threads})")
        ax.set_xlabel("qubits")
        ax.set_ylabel("median wall time [ms]")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
    axes[0][0].legend(fontsize=8, loc="best")
    fig.suptitle("Noisy density-matrix simulation — runtime vs qubits", y=1.02)
    return _save(fig, out_dir, "noise_runtime_vs_qubits.png")


@plotter
def fig_sampling_throughput(data: dict, out_dir: str) -> tuple[str, str]:
    """Shot-sampling throughput (shots/s) for trajectory Monte-Carlo runs."""
    rows = [r for r in _ok(data["results"]) if r.get("group") == "sampling"]
    if not rows:
        return "", ""
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    width = 0.8 / max(1, len({r["threads"] for r in rows}))
    qubits = sorted({r["n_qubits"] for r in rows})
    threads_list = sorted({r["threads"] for r in rows})
    legend_done: set[int] = set()
    xi = 0
    ticks, labels = [], []
    for n in qubits:
        for backend in sorted({r["backend"] for r in rows}):
            base = xi
            for ti, t in enumerate(threads_list):
                r = next((r for r in rows if r["n_qubits"] == n
                          and r["backend"] == backend and r["threads"] == t), None)
                if r is None:
                    continue
                shots_per_s = r["shots"] / (r["stats"]["median_ms"] / 1e3)
                ax.bar(base + ti * width, shots_per_s, width=width * 0.92,
                       color=f"C{ti}",
                       label=f"threads={t}" if t not in legend_done else None)
                legend_done.add(t)
            ticks.append(base + width * (len(threads_list) - 1) / 2)
            labels.append(f"{_label(backend)}\nn={n}")
            xi += 1
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("sampling throughput [shots/s]")
    ax.set_yscale("log")
    ax.set_title("Trajectory sampling (noisy circuit, shots mode)\n"
                 "(missing bars = case timed out; see notes)")
    ax.grid(True, axis="y", which="both", alpha=0.3)
    ax.legend(fontsize=9)
    return _save(fig, out_dir, "sampling_throughput.png")


def plot_all(results_path: str, out_dir: str) -> list[tuple[str, str]]:
    """Render every registered figure from a results JSON.

    Returns ``[(figure_name, output_path)]`` for the figures that produced
    output; figures whose data slice is empty are skipped silently.
    """
    import json

    with open(results_path, encoding="utf-8") as fh:
        data = json.load(fh)
    made = []
    for fn in PLOTTERS:
        out = fn(data, out_dir)
        if out[0]:
            made.append(out)
    return made
