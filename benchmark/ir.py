"""Backend-agnostic circuit intermediate representation.

Every benchmark circuit is compiled to a flat list of :class:`Op` before it
reaches a simulator adapter.  Adapters translate this IR into their native
gate set, so adding a new simulator or a new circuit family never touches the
other side.

Gate names (angles in radians)::

    h, x, y, z, s, sdg, t, tdg                # 1-qubit, no parameters
    rx, ry, rz                                 # 1-qubit, 1 parameter
    cx, cz, swap                               # 2-qubit, no parameters

Noise channel names (inline, applied at their position in the op list)::

    depol1   (q, p)                 1-qubit depolarizing
    depol2   (q1, q2, p)            2-qubit depolarizing
    adamp    (q, gamma)             amplitude damping
    bitflip  (q, p)                 bit flip
"""

from __future__ import annotations

from dataclasses import dataclass, replace

GATE_NAMES = frozenset(
    {"h", "x", "y", "z", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "cx", "cz", "swap"}
)
CHANNEL_NAMES = frozenset({"depol1", "depol2", "adamp", "bitflip"})

GATE_ARITY = {
    "h": 1,
    "x": 1,
    "y": 1,
    "z": 1,
    "s": 1,
    "sdg": 1,
    "t": 1,
    "tdg": 1,
    "rx": 1,
    "ry": 1,
    "rz": 1,
    "cx": 2,
    "cz": 2,
    "swap": 2,
    "depol1": 1,
    "depol2": 2,
    "adamp": 1,
    "bitflip": 1,
}


def is_channel(name: str) -> bool:
    return name in CHANNEL_NAMES


@dataclass(frozen=True)
class Op:
    name: str
    qubits: tuple[int, ...]
    params: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if self.name not in GATE_NAMES and self.name not in CHANNEL_NAMES:
            raise ValueError(f"unknown op {self.name!r}")
        expected = GATE_ARITY[self.name]
        if len(self.qubits) != expected:
            raise ValueError(f"op {self.name!r} expects {expected} qubits, got {self.qubits}")

    @property
    def arity(self) -> int:
        return GATE_ARITY[self.name]


@dataclass(frozen=True)
class Circuit:
    """A flat op list plus metadata. Channels (if any) are inline."""

    name: str
    n_qubits: int
    ops: tuple[Op, ...]
    seed: int | None = None

    def gates(self) -> tuple[Op, ...]:
        return tuple(op for op in self.ops if not is_channel(op.name))

    def channels(self) -> tuple[Op, ...]:
        return tuple(op for op in self.ops if is_channel(op.name))

    def with_seed(self, seed: int) -> Circuit:
        return replace(self, seed=seed)


@dataclass(frozen=True)
class NoisePreset:
    """A noise configuration attached after every gate of matching arity.

    kind == "depolarizing": depol1(p1) after every 1q gate, depol2(p2) after
    every 2q gate.  kind == "amplitude_damping": adamp(gamma) after every 1q
    gate.  kind == "bitflip": bitflip(p1) after every 1q gate.
    """

    name: str
    kind: str = "none"  # none | depolarizing | amplitude_damping | bitflip
    p1: float = 0.0
    p2: float = 0.0
    gamma: float = 0.0


def apply_noise(circuit: Circuit, preset: NoisePreset) -> Circuit:
    """Return a copy of ``circuit`` with inline channels inserted per preset."""

    if preset.kind == "none":
        return circuit
    ops: list[Op] = []
    for op in circuit.ops:
        ops.append(op)
        if is_channel(op.name):
            continue
        if preset.kind == "depolarizing":
            if op.arity == 1:
                ops.append(Op("depol1", op.qubits, (preset.p1,)))
            else:
                ops.append(Op("depol2", op.qubits, (preset.p2,)))
        elif preset.kind == "amplitude_damping":
            for q in op.qubits:
                ops.append(Op("adamp", (q,), (preset.gamma,)))
        elif preset.kind == "bitflip":
            for q in op.qubits:
                ops.append(Op("bitflip", (q,), (preset.p1,)))
    return Circuit(
        name=f"{circuit.name}+{preset.name}",
        n_qubits=circuit.n_qubits,
        ops=tuple(ops),
        seed=circuit.seed,
    )
