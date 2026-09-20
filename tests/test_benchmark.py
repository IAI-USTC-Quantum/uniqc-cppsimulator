"""Unit tests for the benchmark framework itself (no simulator required).

Only exercises the dependency-free modules: IR, circuit families, noise
presets and preset matrices.  Adapter-level correctness is covered by
``python -m benchmark selftest`` in a prepared environment.
"""

from __future__ import annotations

import pytest

from benchmark.ir import Circuit, NoisePreset, Op, apply_noise, is_channel
from benchmark.registry import CIRCUITS, NOISE, register_circuit


def test_op_validates_qubit_arity() -> None:
    with pytest.raises(ValueError, match="expects 2 qubits"):
        Op("cx", (0,))
    with pytest.raises(ValueError, match="expects 2 qubits"):
        Op("depol2", (0,), (0.01,))
    assert Op("depol2", (0, 1), (0.01,)).arity == 2
    with pytest.raises(ValueError, match="unknown op"):
        Op("quantum_frobnicator", (0,))


def test_apply_noise_inserts_channels_per_arity() -> None:
    circuit = Circuit("t", 2, (Op("h", (0,)), Op("cx", (0, 1))))
    noisy = apply_noise(circuit, NoisePreset("depol", kind="depolarizing", p1=0.1, p2=0.2))
    assert [op.name for op in noisy.ops] == ["h", "depol1", "cx", "depol2"]
    assert noisy.ops[1].qubits == (0,) and noisy.ops[1].params == (0.1,)
    assert noisy.ops[3].qubits == (0, 1) and noisy.ops[3].params == (0.2,)

    clean = apply_noise(circuit, NoisePreset("none"))
    assert clean is circuit

    damped = apply_noise(circuit, NoisePreset("ad", kind="amplitude_damping", gamma=0.3))
    assert [op.name for op in damped.ops] == ["h", "adamp", "cx", "adamp", "adamp"]


def test_registered_circuit_families_build_all_qubit_counts() -> None:
    assert {"ghz", "qft", "random", "qaoa"} <= set(CIRCUITS)
    for name, builder in CIRCUITS.items():
        circuit = builder(5, depth=2, seed=7)
        assert circuit.n_qubits == 5
        assert circuit.gates(), f"{name} produced no gates"
        assert all(is_channel(op.name) is False for op in circuit.gates())
        # every op stays in range and repeated builds are identical
        assert all(q < 5 for op in circuit.ops for q in op.qubits)
        assert builder(5, 2, 7).ops == circuit.ops


def test_qft_gate_count_is_quadratic() -> None:
    # n(n-1)/2 CRz * 4 ops + n H + floor(n/2) swaps
    n = 6
    expected = 6 * 5 // 2 * 4 + 6 + 3
    assert len(CIRCUITS["qft"](n, 1, 0).ops) == expected


def test_noise_presets_registered() -> None:
    assert {"none", "depol", "depol-strong", "adamp", "bitflip"} <= set(NOISE)
    assert NOISE["depol"].kind == "depolarizing"


def test_registry_rejects_duplicate_circuit_name() -> None:
    with pytest.raises(ValueError, match="duplicate circuit family"):

        @register_circuit("ghz")
        def _dupe(n: int, d: int, seed: int) -> Circuit:
            return Circuit("x", n, ())
