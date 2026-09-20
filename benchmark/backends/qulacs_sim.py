"""Qulacs adapters (QuantumState / DensityMatrix; OpenMP via env vars).

Qulacs has no Python-level thread API; the runner pins OMP_NUM_THREADS in
the worker environment before import (threads_mode == "env").  Gates are
recorded on a ``qulacs.QuantumCircuit`` once per run and applied with
``update_quantum_state``; the built-in qulacs noise gates realize the inline
channels on the density matrix.  Empirically qubit 0 is the most significant
bit of the flat amplitude index.
"""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_diag, prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def _add_op(circ, gate, op):
    q = op.qubits
    if op.name == "h":
        circ.add_H_gate(q[0])
    elif op.name == "x":
        circ.add_X_gate(q[0])
    elif op.name == "y":
        circ.add_Y_gate(q[0])
    elif op.name == "z":
        circ.add_Z_gate(q[0])
    elif op.name == "s":
        circ.add_S_gate(q[0])
    elif op.name == "sdg":
        circ.add_Sdag_gate(q[0])
    elif op.name == "t":
        circ.add_T_gate(q[0])
    elif op.name == "tdg":
        circ.add_Tdag_gate(q[0])
    elif op.name == "rx":
        circ.add_RX_gate(q[0], op.params[0])
    elif op.name == "ry":
        circ.add_RY_gate(q[0], op.params[0])
    elif op.name == "rz":
        circ.add_RZ_gate(q[0], op.params[0])
    elif op.name == "cx":
        circ.add_CNOT_gate(q[0], q[1])
    elif op.name == "cz":
        circ.add_CZ_gate(q[0], q[1])
    elif op.name == "swap":
        circ.add_SWAP_gate(q[0], q[1])
    elif op.name == "depol1":
        circ.add_gate(gate.DepolarizingNoise(q[0], op.params[0]))
    elif op.name == "depol2":
        circ.add_gate(gate.TwoQubitDepolarizingNoise(q[0], q[1], op.params[0]))
    elif op.name == "adamp":
        circ.add_gate(gate.AmplitudeDampingNoise(q[0], op.params[0]))
    elif op.name == "bitflip":
        circ.add_gate(gate.BitFlipNoise(q[0], op.params[0]))
    else:
        raise ValueError(f"unmapped op {op.name}")  # pragma: no cover


class _QulacsBase(BenchmarkBackend):
    import_name = "qulacs"
    threads_mode = "env"
    homepage = "https://github.com/qulacs/qulacs"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import qulacs
        from qulacs import gate

        circ = qulacs.QuantumCircuit(circuit.n_qubits)
        for op in circuit.ops:
            _add_op(circ, gate, op)
        state = self._new_state(circuit.n_qubits)
        circ.update_quantum_state(state)
        return {"p_q0_1": self._prob(state)}


@register_backend
class QulacsStatevector(_QulacsBase):
    name = "qulacs_sv"
    label = "Qulacs QuantumState"
    kind = "statevector"
    max_qubits = 28

    def _new_state(self, n):
        import qulacs

        return qulacs.QuantumState(n)

    def _prob(self, state) -> float:
        return prob_q0_1_from_statevector(state.get_vector(), q0_is_lsb=True)


@register_backend
class QulacsDensity(_QulacsBase):
    name = "qulacs_dm"
    label = "Qulacs DensityMatrix"
    kind = "density"
    max_qubits = 14
    supports_channels = True

    def _new_state(self, n):
        import qulacs

        return qulacs.DensityMatrix(n)

    def _prob(self, state) -> float:
        return prob_q0_1_from_diag(state.get_matrix(), q0_is_lsb=True)
