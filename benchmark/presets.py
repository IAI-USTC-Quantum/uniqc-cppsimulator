"""Benchmark matrices.

A preset is a list of :class:`Group` slices; the runner expands each group
into concrete cases (backend x circuit x qubits x threads ...), dropping
combinations a backend cannot run (unavailable package, qubit cap, channel
support).  Add a new group or preset here to extend the matrix — nothing else
needs to change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_THREADS = min(8, os.cpu_count() or 1)
SEED = 20260920


@dataclass(frozen=True)
class Group:
    """One slice of a benchmark matrix.

    A group fixes every dimension except the ones it varies: it names the
    backends (or the ``all_sv`` / ``all_dm`` wildcards), the circuit
    families, the qubit sweep, the noise preset, whether shots are sampled,
    and the thread tiers.  ``expand_groups`` turns each group into concrete
    case dicts and drops combinations a backend cannot run.
    """

    name: str  # human-readable group id, also stored on each result record
    backends: tuple[str, ...]  # backend names, or ("all_sv",) / ("all_dm",) wildcards
    circuits: tuple[str, ...] = ("ghz",)  # circuit families (must be registered)
    qubits: tuple[int, ...] = (4, 8)  # qubit-count sweep
    depth: int = 1  # layer depth for parametric families (ghz/qft ignore it)
    noise: str = "none"  # noise preset name (must be registered)
    shots: int = 0  # 0 = exact probabilities, >0 = sampled trajectories
    threads: tuple[int, ...] = (1,)  # thread tiers to expand over
    repeats: int = 3  # timed repetitions per case (after one warm-up)
    timeout_s: int = 300  # per-case worker timeout (runner adds 60 s grace)


PRESETS: dict[str, list[Group]] = {
    "smoke": [
        Group(
            name="ideal-sv",
            backends=("all_sv",),
            circuits=("ghz", "qft", "random"),
            qubits=(4, 8),
            depth=2,
            threads=(1, min(4, DEFAULT_THREADS)),
            repeats=1,
            timeout_s=180,
        ),
        Group(
            name="noise-dm",
            backends=("all_dm",),
            circuits=("random",),
            qubits=(4,),
            depth=2,
            noise="depol",
            threads=(1,),
            repeats=1,
            timeout_s=180,
        ),
        Group(
            name="sampling",
            backends=("uniqc_sv", "aer_sv"),
            circuits=("random",),
            qubits=(8,),
            depth=2,
            noise="depol",
            shots=128,
            threads=(1, min(4, DEFAULT_THREADS)),
            repeats=1,
            timeout_s=180,
        ),
    ],
    "standard": [
        Group(
            name="ideal-sv",
            backends=("all_sv",),
            circuits=("ghz", "qft", "random", "qaoa"),
            qubits=(4, 8, 12, 16, 20, 24),
            depth=4,
            threads=(1, DEFAULT_THREADS),
            repeats=3,
            timeout_s=420,
        ),
        Group(
            name="noise-dm",
            backends=("all_dm",),
            circuits=("random",),
            qubits=(4, 6, 8, 10),
            depth=2,
            noise="depol",
            threads=(1, DEFAULT_THREADS),
            repeats=3,
            timeout_s=300,
        ),
        Group(
            name="noise-dm-variants",
            backends=("all_dm",),
            circuits=("random",),
            qubits=(8,),
            depth=2,
            noise="adamp",
            threads=(1,),
            repeats=3,
            timeout_s=300,
        ),
        Group(
            name="noise-dm-bitflip",
            backends=("all_dm",),
            circuits=("random",),
            qubits=(8,),
            depth=2,
            noise="bitflip",
            threads=(1,),
            repeats=3,
            timeout_s=300,
        ),
        Group(
            name="sampling",
            backends=("uniqc_sv", "aer_sv"),
            circuits=("random",),
            qubits=(8, 16, 20),
            depth=2,
            noise="depol",
            shots=1024,
            threads=(1, DEFAULT_THREADS),
            repeats=3,
            timeout_s=600,
        ),
    ],
}
