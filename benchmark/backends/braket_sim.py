"""Amazon Braket local simulator adapter (pure NumPy/SciPy reference speed)."""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def build_braket_circuit(circuit: Circuit):
    from braket.circuits import Circuit

    c = Circuit()
    for op in circuit.ops:
        q = op.qubits
        if op.name == "h":
            c.h(q[0])
        elif op.name == "x":
            c.x(q[0])
        elif op.name == "y":
            c.y(q[0])
        elif op.name == "z":
            c.z(q[0])
        elif op.name == "s":
            c.s(q[0])
        elif op.name == "sdg":
            c.si(q[0])
        elif op.name == "t":
            c.t(q[0])
        elif op.name == "tdg":
            c.ti(q[0])
        elif op.name in ("rx", "ry", "rz"):
            getattr(c, op.name)(q[0], op.params[0])
        elif op.name == "cx":
            c.cnot(q[0], q[1])
        elif op.name == "cz":
            c.cz(q[0], q[1])
        elif op.name == "swap":
            c.swap(q[0], q[1])
        else:
            raise ValueError(f"unmapped op {op.name}")  # pragma: no cover
    # shots=0 + state_vector() gives exact amplitudes (qubit 0 = LSB).
    c.state_vector()
    return c


@register_backend
class BraketLocalSimulator(BenchmarkBackend):
    name = "braket_sv"
    label = "Braket LocalSimulator (NumPy)"
    import_name = "braket"
    kind = "statevector"
    threads_mode = "env"  # BLAS threads
    max_qubits = 18
    homepage = "https://github.com/amazon-braket/amazon-braket-default-simulator-python"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        from braket.devices import LocalSimulator

        dev = LocalSimulator(backend="default")
        result = dev.run(build_braket_circuit(circuit), shots=0).result()
        vec = result.result_types[0].value
        return {"p_q0_1": prob_q0_1_from_statevector(vec, q0_is_lsb=True)}
