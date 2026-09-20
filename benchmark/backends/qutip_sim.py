"""QuTiP adapter (qutip-qip CircuitSimulator, sequential sparse application).

QuTiP is a general open-system framework, not a circuit-simulator speed
daemon; it is included as a scientific-computing reference point.  Phase
gates use exact ``PHASEGATE`` instructions.
"""

from __future__ import annotations

import math

import numpy as np

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


@register_backend
class QuTiPSimulator(BenchmarkBackend):
    name = "qutip"
    label = "QuTiP qip CircuitSimulator"
    import_name = "qutip_qip"
    kind = "statevector"
    threads_mode = "env"  # BLAS threads
    max_qubits = 12
    homepage = "https://github.com/qutip/qutip"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import qutip
        from qutip.qip.circuit import CircuitSimulator, QubitCircuit

        qc = QubitCircuit(circuit.n_qubits)
        for op in circuit.ops:
            q = op.qubits
            if op.name == "h":
                qc.add_gate("SNOT", targets=q[0])
            elif op.name in ("x", "y", "z"):
                qc.add_gate(op.name.upper(), targets=q[0])
            elif op.name in ("s", "sdg", "t", "tdg"):
                theta = {"s": math.pi / 2, "sdg": -math.pi / 2, "t": math.pi / 4, "tdg": -math.pi / 4}[op.name]
                qc.add_gate("PHASEGATE", targets=q[0], arg_value=theta)
            elif op.name in ("rx", "ry", "rz"):
                qc.add_gate(op.name.upper(), targets=q[0], arg_value=op.params[0])
            elif op.name == "cx":
                qc.add_gate("CNOT", controls=q[0], targets=q[1])
            elif op.name == "cz":
                qc.add_gate("CZ", controls=q[0], targets=q[1])
            elif op.name == "swap":
                qc.add_gate("SWAP", targets=list(q))
            else:
                raise ValueError(f"unmapped op {op.name}")  # pragma: no cover

        sim = CircuitSimulator(qc)
        state = qutip.tensor([qutip.basis(2, 0)] * circuit.n_qubits)
        final = sim.run(state).final_states[0]
        vec = np.asarray(final.full()).ravel()
        return {"p_q0_1": prob_q0_1_from_statevector(vec, q0_is_lsb=False)}
