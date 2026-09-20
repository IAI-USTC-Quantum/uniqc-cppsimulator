"""Google qsim adapter via qsimcirq (C++ kernel, OpenMP threads)."""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


@register_backend
class QsimCirq(BenchmarkBackend):
    name = "qsimcirq"
    label = "Google qsim (qsimcirq)"
    import_name = "qsimcirq"
    kind = "statevector"
    threads_mode = "option"
    max_qubits = 30
    homepage = "https://github.com/quantumlib/qsim"

    def __init__(self, threads: int = 1) -> None:
        super().__init__(threads)
        import qsimcirq

        self._sim = qsimcirq.QSimSimulator(qsim_options={"t": threads})

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        from benchmark.backends.cirq_sim import build_cirq_circuit

        # qsim has no S†/T† instructions; phase_via_rz swaps in Rz equivalents
        # (identical up to global phase, so probabilities are unchanged).
        cc, qubits = build_cirq_circuit(circuit, with_channels=False, phase_via_rz=True)
        vec = self._sim.simulate(cc, qubit_order=qubits).final_state_vector
        return {"p_q0_1": prob_q0_1_from_statevector(vec, q0_is_lsb=False)}
