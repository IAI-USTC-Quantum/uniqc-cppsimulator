"""Tests for the uniqc_cpp pybind11 extension.

This suite exercises the native extension directly, without any dependency
on the ``uniqc`` Python package. It includes:

- smoke tests for the two simulator backends (statevector / density
  operator), measurement, and the global RNG;
- QRAM argument validation (migrated from UnifiedQuantum's
  ``uniqc/test/core/test_qram.py``);
- global-control range validation (migrated from UnifiedQuantum's
  ``uniqc/test/core/test_originir_control_validation.py``).
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import uniqc_cpp

SIMULATORS = ["StatevectorSimulator", "DensityOperatorSimulator"]


def make_sim(name: str, n_qubits: int = 2):
    sim = getattr(uniqc_cpp, name)()
    sim.init_n_qubit(n_qubits)
    return sim


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("simulator_name", SIMULATORS)
def test_init_ground_state(simulator_name: str) -> None:
    sim = make_sim(simulator_name, 2)
    assert sim.get_prob(0, 0) == pytest.approx(1.0)
    assert sim.get_prob(1, 0) == pytest.approx(1.0)


@pytest.mark.parametrize("simulator_name", SIMULATORS)
def test_x_flips_qubit(simulator_name: str) -> None:
    sim = make_sim(simulator_name, 2)
    sim.x(0)
    assert sim.get_prob(0, 1) == pytest.approx(1.0)
    assert sim.get_prob(1, 0) == pytest.approx(1.0)


@pytest.mark.parametrize("simulator_name", SIMULATORS)
def test_hadamard_splits_probability(simulator_name: str) -> None:
    sim = make_sim(simulator_name, 1)
    sim.hadamard(0)
    assert sim.get_prob(0, 0) == pytest.approx(0.5)
    assert sim.get_prob(0, 1) == pytest.approx(0.5)


def test_bell_state_probabilities() -> None:
    sim = make_sim("StatevectorSimulator", 2)
    sim.hadamard(0)
    sim.cnot(0, 1)
    probs = sim.pmeasure([0, 1])
    assert list(probs) == pytest.approx([0.5, 0.0, 0.0, 0.5])


def test_statevector_total_qubit_and_state() -> None:
    sim = make_sim("StatevectorSimulator", 3)
    assert sim.total_qubit == 3
    assert len(sim.state) == 8
    assert abs(sim.state[0]) == pytest.approx(1.0)


@pytest.mark.parametrize("simulator_name", SIMULATORS)
def test_max_qubit_num_readonly(simulator_name: str) -> None:
    cls = getattr(uniqc_cpp, simulator_name)
    assert isinstance(cls.max_qubit_num, int)
    with pytest.raises(AttributeError):
        cls.max_qubit_num = 1


def test_seed_makes_rand_deterministic() -> None:
    uniqc_cpp.seed(20260821)
    first = uniqc_cpp.rand()
    uniqc_cpp.seed(20260821)
    second = uniqc_cpp.rand()
    assert first == second
    assert 0.0 <= first < 1.0


# ---------------------------------------------------------------------------
# Global-control validation (migrated from test_originir_control_validation.py)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("simulator_name", SIMULATORS)
def test_simulator_rejects_out_of_range_global_control(simulator_name: str) -> None:
    simulator = make_sim(simulator_name, 2)
    with pytest.raises(ValueError, match=r"control_qubit = 999"):
        simulator.x(0, [999], False)


# ---------------------------------------------------------------------------
# QRAM validation (migrated from test_qram.py)
# ---------------------------------------------------------------------------


def test_qram_duplicate_addr_qubit_rejected() -> None:
    sim = make_sim("StatevectorSimulator", 6)
    with pytest.raises(ValueError, match="duplicated in the address"):
        sim.qram([0, 0, 1], [2, 3], [0] * 8)


def test_qram_duplicate_data_qubit_rejected() -> None:
    sim = make_sim("StatevectorSimulator", 6)
    with pytest.raises(ValueError, match="duplicated in the data"):
        sim.qram([0, 1], [2, 2, 3], [0] * 8)


def test_qram_addr_data_overlap_rejected() -> None:
    sim = make_sim("StatevectorSimulator", 6)
    with pytest.raises(ValueError, match="overlaps with an address qubit"):
        sim.qram([0, 1], [1, 3], [0] * 4)


def test_qram_duplicate_control_qubit_rejected() -> None:
    sim = make_sim("StatevectorSimulator", 6)
    with pytest.raises(ValueError, match="duplicated in the control"):
        sim.qram([0, 1], [2, 3], [0] * 4, [4, 4])


def test_qram_control_overlap_rejected() -> None:
    sim = make_sim("StatevectorSimulator", 6)
    with pytest.raises(ValueError, match="overlaps with an address/data qubit"):
        sim.qram([0, 1], [2, 3], [0] * 4, [1])


def test_qram_valid_call_succeeds_on_both_backends() -> None:
    sv = make_sim("StatevectorSimulator", 6)
    sv.qram([0, 1], [2, 3], [0] * 4, [4, 5])

    dm = make_sim("DensityOperatorSimulator", 6)
    dm.qram([0, 1], [2, 3], [0] * 4, [4, 5])


# ---------------------------------------------------------------------------
# Noise-channel regressions
# ---------------------------------------------------------------------------


def _twoqubit_depolarizing_error_rate(p: float, shots: int = 2000) -> float:
    """Measured error rate of X(0); ISWAP(0,1); twoqubit_depolarizing(p).

    The ideal outcome is |01> (integer 2). Of the 15 two-qubit Pauli errors,
    the phase-only ones (ZI, IZ, ZZ) preserve the computational-basis
    outcome, so the expected error rate is (1 - 3/15) * p = 0.8 * p.
    """
    errors = 0
    for _ in range(shots):
        sim = make_sim("StatevectorSimulator", 2)
        sim.x(0)
        sim.iswap(0, 1)
        sim.twoqubit_depolarizing(0, 1, p)
        if sim.measure_single_shot([0, 1]) != 2:
            errors += 1
    return errors / shots


def test_measure_single_shot_scalar_overload_returns() -> None:
    """Regression: the scalar overload forwards to the list overload.

    Up to 1.0.1 it forwarded through a braced init-list that overload
    resolution matched back to the scalar overload itself — a perfect tail
    recursion the compiler turns into an infinite loop (the process hangs,
    it does not crash).  Run in a subprocess with a timeout so a regression
    fails the test instead of hanging the suite.
    """
    code = (
        "import uniqc_cpp\n"
        "def fresh():\n"
        "    s = uniqc_cpp.StatevectorSimulator()\n"
        "    s.init_n_qubit(2)\n"
        "    s.hadamard(0)\n"
        "    return s\n"
        "assert fresh().measure_single_shot(0) in (0, 1)\n"
        "# deterministic: scalar and list overloads must sample identically\n"
        "uniqc_cpp.seed(7); a = fresh().measure_single_shot([0])\n"
        "uniqc_cpp.seed(7); b = fresh().measure_single_shot(0)\n"
        "assert a == b\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )
    assert proc.returncode == 0, proc.stderr


def test_twoqubit_depolarizing_probability_applies_per_call() -> None:
    """Regression: each call must honour its own ``p``.

    In 1.0.0 the Kraus probability vector inside
    ``StatevectorSimulator::twoqubit_depolarizing`` was a ``const static``
    local, initialised once per process: the first call's ``p`` silently
    applied to every later call. Interleave low/high ``p`` in both orders
    within one process and check each batch matches its own expectation
    (0.8 * p for this probe).
    """
    for first, second in ((0.1, 0.9), (0.9, 0.1)):
        uniqc_cpp.seed(20260823)
        low_or_high_first = _twoqubit_depolarizing_error_rate(first)
        uniqc_cpp.seed(20260823)
        low_or_high_second = _twoqubit_depolarizing_error_rate(second)
        rates = {first: low_or_high_first, second: low_or_high_second}
        assert rates[0.1] == pytest.approx(0.08, abs=0.02)
        assert rates[0.9] == pytest.approx(0.72, abs=0.04)
