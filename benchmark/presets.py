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
    name: str
    backends: tuple[str, ...]  # backend names, or ("all_sv",) / ("all_dm",) wildcards
    circuits: tuple[str, ...] = ("ghz",)
    qubits: tuple[int, ...] = (4, 8)
    depth: int = 1
    noise: str = "none"
    shots: int = 0
    threads: tuple[int, ...] = (1,)
    repeats: int = 3
    timeout_s: int = 300


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
