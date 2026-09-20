"""Qibo adapter (qibojit numba backend, qibo.set_threads)."""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def build_qibo_circuit(circuit: Circuit):
    import qibo
    import qibo.gates as qg

    gate_cls = {
        "h": qg.H, "x": qg.X, "y": qg.Y, "z": qg.Z,
        "s": qg.S, "sdg": qg.SDG, "t": qg.T, "tdg": qg.TDG,
        "rx": qg.RX, "ry": qg.RY, "rz": qg.RZ,
        "cx": qg.CNOT, "cz": qg.CZ, "swap": qg.SWAP,
    }
    c = qibo.models.Circuit(circuit.n_qubits)
    for op in circuit.ops:
        if op.name in ("rx", "ry", "rz"):
            c.add(gate_cls[op.name](op.qubits[0], op.params[0]))
        else:
            c.add(gate_cls[op.name](*op.qubits))
    return c


@register_backend
class QiboSimulator(BenchmarkBackend):
    name = "qibo"
    label = "Qibo (qibojit)"
    import_name = "qibo"
    kind = "statevector"
    threads_mode = "option"
    max_qubits = 30
    homepage = "https://github.com/qiboteam/qibo"

    def set_threads(self, n: int) -> None:
        import qibo

        qibo.set_threads(n)

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import numpy as np

        c = build_qibo_circuit(circuit)
        result = c()
        probs = np.asarray(result.probabilities(qubits=[0])).reshape(-1)
        return {"p_q0_1": float(probs[1])}
