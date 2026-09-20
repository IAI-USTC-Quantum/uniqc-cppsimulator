"""Quimb adapter (dense statevector via ``quimb.tensor.Circuit``)."""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend

_ONE_Q_PARAM = {"rx", "ry", "rz"}


@register_backend
class QuimbSimulator(BenchmarkBackend):
    name = "quimb"
    label = "quimb dense Circuit"
    import_name = "quimb"
    kind = "statevector"
    threads_mode = "env"  # BLAS threads
    max_qubits = 18
    homepage = "https://github.com/jcmgray/quimb"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        from quimb.tensor import Circuit

        circ = Circuit(circuit.n_qubits)
        for op in circuit.ops:
            if op.name in _ONE_Q_PARAM:
                circ.apply_gate(op.name, op.params[0], op.qubits[0])
            else:
                circ.apply_gate(op.name, *op.qubits)
        psi = circ.to_dense()
        return {"p_q0_1": prob_q0_1_from_statevector(psi, q0_is_lsb=False)}
