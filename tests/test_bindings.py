"""Tests for the uniqc_cpp pybind11 extension.

This suite exercises the native extension directly, without any dependency
on the ``uniqc`` Python package. It includes:

- smoke tests for the two simulator backends (statevector / density
  operator), measurement, and the global RNG;
- global multithreading control (switch, thread count, parallel-vs-serial
  equivalence);
- QRAM argument validation (migrated from UnifiedQuantum's
  ``uniqc/test/core/test_qram.py``);
- global-control range validation (migrated from UnifiedQuantum's
  ``uniqc/test/core/test_originir_control_validation.py``).
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

import uniqc_cpp

SIMULATORS = ["StatevectorSimulator", "DensityOperatorSimulator"]


@pytest.fixture(autouse=True)
def _serial_threading_defaults():
    """Kernel threading is off around every test (the library default)."""
    uniqc_cpp.set_num_threads(1)
    uniqc_cpp.set_parallel_enabled(False)
    yield
    uniqc_cpp.set_num_threads(1)
    uniqc_cpp.set_parallel_enabled(False)


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

# ---------------------------------------------------------------------------
# Global multithreading control
# ---------------------------------------------------------------------------


def test_threading_defaults_and_switch() -> None:
    assert uniqc_cpp.is_parallel_enabled() is False
    assert uniqc_cpp.get_num_threads() == 1

    uniqc_cpp.set_parallel_enabled(True)
    assert uniqc_cpp.is_parallel_enabled() is True
    uniqc_cpp.set_parallel_enabled(False)
    assert uniqc_cpp.is_parallel_enabled() is False

    n = min(4, os.cpu_count() or 1)
    uniqc_cpp.set_num_threads(n)
    assert uniqc_cpp.get_num_threads() == n

    # above hardware concurrency the count is clamped, not rejected
    uniqc_cpp.set_num_threads((os.cpu_count() or 1) + 1000)
    assert uniqc_cpp.get_num_threads() == (os.cpu_count() or 1)

    with pytest.raises(ValueError):
        uniqc_cpp.set_num_threads(0)


def _run_mixed_circuit(name: str, n_qubits: int):
    """A circuit touching 1q/2q/3q gates, parametric gates and controls."""
    sim = getattr(uniqc_cpp, name)()
    sim.init_n_qubit(n_qubits)
    for q in range(n_qubits):
        sim.hadamard(q)
    for q in range(n_qubits):
        sim.rz(q, 0.3 * (q + 1))
    sim.x(0)
    sim.y(1)
    sim.z(2)
    sim.s(3)
    sim.t(4)
    sim.cnot(0, 1)
    sim.cz(1, 2)
    sim.swap(2, 3)
    sim.iswap(3, 4)
    sim.xy(4, 5, 0.7)
    sim.xx(5, 6, 0.2)
    sim.yy(6, 7, 0.4)
    sim.zz(7, 8, 0.9)
    sim.toffoli(0, 1, 9)
    sim.cswap(2, 10, 11)
    sim.phase2q(12, 13, 0.1, 0.2, 0.3)
    sim.hadamard(1, [13])  # gate with a global controller
    sim.cnot(2, 3, [12])
    sim.xy(5, 6, 0.25, [0], dagger=True)
    return sim


def test_parallel_gates_match_serial_bitwise() -> None:
    """Gate kernels have no reductions, so the parallel state must be
    bit-for-bit identical to the serial one (14 qubits = 2^14 amplitudes
    crosses the MIN_PARALLEL_WORK threshold, exercising real threads)."""
    n_qubits = 14
    serial = _run_mixed_circuit("StatevectorSimulator", n_qubits)
    state_serial = serial.state

    uniqc_cpp.set_num_threads(min(8, os.cpu_count() or 1))
    uniqc_cpp.set_parallel_enabled(True)
    parallel = _run_mixed_circuit("StatevectorSimulator", n_qubits)

    assert parallel.state == state_serial


def test_parallel_readouts_match_serial_approximately() -> None:
    """Probability readouts sum amplitudes in chunk order, so only
    floating-point-order differences are allowed (~1e-15 relative)."""
    n_qubits = 14
    uniqc_cpp.set_num_threads(min(8, os.cpu_count() or 1))
    uniqc_cpp.set_parallel_enabled(True)
    parallel = _run_mixed_circuit("StatevectorSimulator", n_qubits)

    uniqc_cpp.set_parallel_enabled(False)
    serial = _run_mixed_circuit("StatevectorSimulator", n_qubits)

    assert parallel.pmeasure([0, 1]) == pytest.approx(
        serial.pmeasure([0, 1]), rel=1e-9, abs=1e-12)
    assert parallel.pmeasure(0) == pytest.approx(serial.pmeasure(0), rel=1e-9, abs=1e-12)
    assert parallel.get_prob(0, 1) == pytest.approx(serial.get_prob(0, 1), rel=1e-9, abs=1e-12)
    assert parallel.get_prob({0: 1, 3: 0}) == pytest.approx(
        serial.get_prob({0: 1, 3: 0}), rel=1e-9, abs=1e-12)


def test_parallel_measure_qubit_reproducible_across_thread_counts() -> None:
    """rand() is drawn on the calling thread, so measurement outcomes must
    not depend on the kernel thread count."""
    uniqc_cpp.seed(20260921)
    serial = _run_mixed_circuit("StatevectorSimulator", 14)
    outcome_serial = serial.measure_qubit(1)

    uniqc_cpp.set_num_threads(min(8, os.cpu_count() or 1))
    uniqc_cpp.set_parallel_enabled(True)
    uniqc_cpp.seed(20260921)
    parallel = _run_mixed_circuit("StatevectorSimulator", 14)
    outcome_parallel = parallel.measure_qubit(1)

    assert outcome_parallel == outcome_serial
    assert parallel.pmeasure(1) == pytest.approx(serial.pmeasure(1), rel=1e-9)


def test_parallel_density_operator_matches_serial() -> None:
    """The density-matrix row loops parallelize too (8 qubits: N^2 = 64k
    matrix elements reaches the work threshold via the per-row hint)."""
    def build() -> list[float]:
        sim = uniqc_cpp.DensityOperatorSimulator()
        sim.init_n_qubit(8)
        for q in range(8):
            sim.hadamard(q)
        for q in range(7):
            sim.cnot(q, q + 1)
            sim.depolarizing(q, 0.01)
        return sim.pmeasure([0, 1])

    serial = build()

    uniqc_cpp.set_num_threads(min(8, os.cpu_count() or 1))
    uniqc_cpp.set_parallel_enabled(True)
    assert build() == pytest.approx(serial, rel=1e-9, abs=1e-12)
