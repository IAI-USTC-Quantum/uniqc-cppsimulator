"""PennyLane lightning.qubit adapter (C++/OpenMP kernel via OMP env)."""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def build_pl_tape(circuit: Circuit):
    """Compile IR gates (channels unsupported) to a PennyLane QuantumScript
    measuring ``probs(wires=0)``."""
    import pennylane as qml

    ops = []
    for op in circuit.ops:
        q = op.qubits
        if op.name == "h":
            ops.append(qml.Hadamard(wires=q[0]))
        elif op.name == "x":
            ops.append(qml.X(wires=q[0]))
        elif op.name == "y":
            ops.append(qml.Y(wires=q[0]))
        elif op.name == "z":
            ops.append(qml.Z(wires=q[0]))
        elif op.name == "s":
            ops.append(qml.S(wires=q[0]))
        elif op.name == "sdg":
            ops.append(qml.adjoint(qml.S(wires=q[0])))
        elif op.name == "t":
            ops.append(qml.T(wires=q[0]))
        elif op.name == "tdg":
            ops.append(qml.adjoint(qml.T(wires=q[0])))
        elif op.name in ("rx", "ry", "rz"):
            ops.append(getattr(qml, op.name.upper())(op.params[0], wires=q[0]))
        elif op.name == "cx":
            ops.append(qml.CNOT(wires=[q[0], q[1]]))
        elif op.name == "cz":
            ops.append(qml.CZ(wires=[q[0], q[1]]))
        elif op.name == "swap":
            ops.append(qml.SWAP(wires=[q[0], q[1]]))
        else:
            raise ValueError(f"unmapped op {op.name}")  # pragma: no cover
    return qml.tape.QuantumScript(ops, [qml.probs(wires=0)])


@register_backend
class PennyLaneLightning(BenchmarkBackend):
    name = "lightning"
    label = "PennyLane lightning.qubit"
    import_name = "pennylane"
    kind = "statevector"
    threads_mode = "env"
    max_qubits = 28
    homepage = "https://github.com/PennyLaneAI/pennylane-lightning"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import pennylane as qml

        dev = qml.device("lightning.qubit", wires=circuit.n_qubits, shots=None)
        probs = dev.execute(build_pl_tape(circuit))
        return {"p_q0_1": float(probs[1])}
