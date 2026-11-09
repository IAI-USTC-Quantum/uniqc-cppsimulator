"""Unit tests for the benchmark framework itself.

The IR / circuit-family / noise-preset / matrix tests are dependency-free;
the CLI ``selftest`` semantics tests import ``benchmark.cli`` and therefore
need the ``uniqc_cpp`` extension itself (as ``tests/test_bindings.py`` does;
external comparison simulators are never required).  Adapter-level
correctness is covered by ``python -m benchmark selftest`` in a prepared
environment.
"""

from __future__ import annotations

import json

import pytest

from benchmark.backends.base import BenchmarkBackend
from benchmark.ir import Circuit, NoisePreset, Op, apply_noise, is_channel
from benchmark.registry import CIRCUITS, NOISE, register_backend, register_circuit


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


# ---------------------------------------------------------------------------
# CLI selftest semantics (benchmark.cli.cmd_selftest)
# ---------------------------------------------------------------------------


class _ProbeBackend(BenchmarkBackend):
    """Registration helper for CLI tests; removed again in ``finally``."""

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:  # pragma: no cover
        raise AssertionError("probe backends never execute circuits")


def _cli_with_stubbed_worker(monkeypatch, backend_cls, worker_results):
    from benchmark import cli

    if backend_cls is not None:
        register_backend(backend_cls)
    monkeypatch.setattr(cli.runner, "selftest_backends", lambda names: worker_results)
    return cli


def test_selftest_skips_uninstalled_backends(monkeypatch, capsys) -> None:
    """Uninstalled simulators are 'missing', not failures (same filter as run)."""
    from benchmark.registry import BACKENDS

    class _Missing(_ProbeBackend):
        name = "_cli_missing"
        import_name = "definitely_not_installed_module_xyz"

    cli = _cli_with_stubbed_worker(
        monkeypatch, _Missing,
        worker_results={"_cli_missing": {"selftest": "fail", "cases": []}},
    )
    try:
        cli.main(["selftest", "--backends", "_cli_missing"])  # must not SystemExit
        out = capsys.readouterr().out
        assert "_cli_missing" in out
        assert "missing (" in out
    finally:
        del BACKENDS["_cli_missing"]


def test_selftest_fails_on_reachable_backend_failing_known_answer(
    monkeypatch, capsys
) -> None:
    from benchmark.registry import BACKENDS

    class _Failing(_ProbeBackend):
        name = "_cli_failing"

    cli = _cli_with_stubbed_worker(
        monkeypatch, _Failing,
        worker_results={"_cli_failing": {"selftest": "fail", "cases": []}},
    )
    try:
        with pytest.raises(SystemExit) as exc:
            cli.main(["selftest", "--backends", "_cli_failing"])
        assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "fail" in out
    finally:
        del BACKENDS["_cli_failing"]


def test_selftest_rejects_unknown_backend_name(monkeypatch, capsys) -> None:
    cli = _cli_with_stubbed_worker(monkeypatch, None, worker_results={})
    with pytest.raises(SystemExit) as exc:
        cli.main(["selftest", "--backends", "no_such_backend"])
    assert exc.value.code == 1
    assert "unknown backend name" in capsys.readouterr().out


def test_worker_selftest_reports_construction_errors_as_data(capsys) -> None:
    """A backend whose constructor raises must yield a JSON record, not a
    bare traceback (the old code left the worker without output, which the
    runner recorded as a subprocess error instead of a selftest failure)."""
    from benchmark.registry import BACKENDS
    from benchmark.worker import run_selftest

    class _Broken(_ProbeBackend):
        name = "_worker_broken"

        def __init__(self, threads: int = 1) -> None:
            raise RuntimeError("boom")

    register_backend(_Broken)
    try:
        run_selftest("_worker_broken")
    finally:
        del BACKENDS["_worker_broken"]
    record = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert record["selftest"] == "fail"
    assert "during construction" in record["cases"][0]["error"]
