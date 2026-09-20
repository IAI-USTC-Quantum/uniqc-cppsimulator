"""Circuit families used by the benchmark.

Each builder returns a :class:`~benchmark.ir.Circuit` built from the shared
IR, so every backend executes an identical gate sequence.  ``depth`` scales
the gate count of the parametric families (ghz/qft ignore it).
"""

from __future__ import annotations

import math
import random

from benchmark.ir import Circuit, Op
from benchmark.registry import register_circuit


def _crz(ops: list[Op], control: int, target: int, theta: float) -> None:
    """Controlled-Rz(theta) decomposed into CX / Rz (up to global phase)."""
    ops.append(Op("rz", (target,), (theta / 2,)))
    ops.append(Op("cx", (control, target)))
    ops.append(Op("rz", (target,), (-theta / 2,)))
    ops.append(Op("cx", (control, target)))


@register_circuit("ghz")
def ghz(n_qubits: int, depth: int = 1, seed: int = 0) -> Circuit:
    """H on q0 then a CNOT chain: the classic fixed-overhead entangler."""
    ops = [Op("h", (0,))]
    for q in range(n_qubits - 1):
        ops.append(Op("cx", (q, q + 1)))
    return Circuit("ghz", n_qubits, tuple(ops), seed)


@register_circuit("qft")
def qft(n_qubits: int, depth: int = 1, seed: int = 0) -> Circuit:
    """Quantum Fourier transform, ~n^2 CRz decomposed to 2 CX each + swaps."""
    ops: list[Op] = []
    for target in range(n_qubits - 1, -1, -1):
        ops.append(Op("h", (target,)))
        for control in range(target - 1, -1, -1):
            k = target - control
            _crz(ops, control, target, math.pi / 2**k)
    for q in range(n_qubits // 2):
        ops.append(Op("swap", (q, n_qubits - 1 - q)))
    return Circuit("qft", n_qubits, tuple(ops), seed)


@register_circuit("random")
def random_layered(n_qubits: int, depth: int = 4, seed: int = 0) -> Circuit:
    """Layered random circuit: per layer random rx/ry/rz on every qubit
    followed by a CNOT ring.  Scales with ``depth``."""
    rng = random.Random(seed)
    ops: list[Op] = []
    for _ in range(depth):
        for q in range(n_qubits):
            g = rng.choice(("rx", "ry", "rz"))
            ops.append(Op(g, (q,), (rng.uniform(0.0, 2.0 * math.pi),)))
        for q in range(n_qubits):
            ops.append(Op("cx", (q, (q + 1) % n_qubits)))
    return Circuit("random", n_qubits, tuple(ops), seed)


@register_circuit("qaoa")
def qaoa(n_qubits: int, depth: int = 3, seed: int = 0) -> Circuit:
    """QAOA-style ansatz on a ring: uniform-H, then per layer
    ZZ(θ_i) on ring edges (CX-RZ-CX) + RX(θ) on every qubit."""
    rng = random.Random(seed)
    ops: list[Op] = [Op("h", (q,)) for q in range(n_qubits)]
    for _ in range(depth):
        for q in range(n_qubits):
            theta = rng.uniform(0.0, math.pi)
            t = q + 1 if q + 1 < n_qubits else 0
            ops.append(Op("cx", (q, t)))
            ops.append(Op("rz", (t,), (theta,)))
            ops.append(Op("cx", (q, t)))
        for q in range(n_qubits):
            ops.append(Op("rx", (q,), (rng.uniform(0.0, 2.0 * math.pi),)))
    return Circuit("qaoa", n_qubits, tuple(ops), seed)
