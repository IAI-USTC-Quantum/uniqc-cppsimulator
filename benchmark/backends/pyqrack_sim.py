"""PyQrack adapter (Qrack hybrid stabilizer/statevector engine).

Kept for reuse on machines where the native Qrack shared library
(``libqrack_pinvoke.so`` under ``/usr/lib/qrack``) is installed; the
availability probe skips it automatically otherwise.  API mapping follows the
PyQrack examples (adjoint phase gates via ``adjoint_s``/``adjoint_t``).
"""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.ir import Circuit
from benchmark.registry import register_backend


@register_backend
class PyQrack(BenchmarkBackend):
    name = "pyqrack"
    label = "Qrack (pyqrack)"
    import_name = "pyqrack"
    kind = "statevector"
    threads_mode = "none"
    max_qubits = 30
    homepage = "https://github.com/unitaryfund/pyqrack"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        from pyqrack import QrackSimulator

        sim = QrackSimulator(circuit.n_qubits)
        for op in circuit.ops:
            q = op.qubits
            if op.name == "h":
                sim.h(q[0])
            elif op.name in ("x", "y", "z"):
                getattr(sim, op.name)(q[0])
            elif op.name == "s":
                sim.s(q[0])
            elif op.name == "sdg":
                sim.adjoint_s(q[0])
            elif op.name == "t":
                sim.t(q[0])
            elif op.name == "tdg":
                sim.adjoint_t(q[0])
            elif op.name in ("rx", "ry", "rz"):
                getattr(sim, op.name)(op.params[0], q[0])
            elif op.name == "cx":
                sim.mcx([q[0]], q[1])
            elif op.name == "cz":
                sim.mcz([q[0]], q[1])
            elif op.name == "swap":
                sim.swap(q[0], q[1])
            else:
                raise ValueError(f"unmapped op {op.name}")  # pragma: no cover
        return {"p_q0_1": float(sim.prob(0))}
