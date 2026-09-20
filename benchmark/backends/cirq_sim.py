"""Cirq adapters (pure-NumPy Simulator / DensityMatrixSimulator).

Cirq amplitude indexing is big-endian w.r.t. ``qubit_order``: the first qubit
in the order is the most significant bit, so qubit 0 lives on the last axis.
Phase gates S/T are exact; noise channels are only supported on the density
backend (inline Cirq noise ops).
"""

from __future__ import annotations

import math

from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_diag, prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def build_cirq_circuit(circuit: Circuit, with_channels: bool, phase_via_rz: bool = False):
    """Compile IR to a ``cirq.Circuit`` plus its qubit order.

    ``with_channels`` inlines the noise channel ops (density backend only).
    ``phase_via_rz`` swaps S/T-family gates for phase-equivalent Rz so
    backends without S†/T† instructions (qsim) can still run the circuit
    identically up to global phase.
    """
    import cirq

    qubits = cirq.LineQubit.range(circuit.n_qubits)
    ops = []
    for op in circuit.ops:
        q = [qubits[i] for i in op.qubits]
        if op.name == "h":
            ops.append(cirq.H.on(q[0]))
        elif op.name == "x":
            ops.append(cirq.X.on(q[0]))
        elif op.name == "y":
            ops.append(cirq.Y.on(q[0]))
        elif op.name == "z":
            ops.append(cirq.Z.on(q[0]))
        elif op.name in ("s", "sdg", "t", "tdg") and phase_via_rz:
            # S = Rz(pi/2), T = Rz(pi/4) up to a global phase.
            theta = {"s": math.pi / 2, "sdg": -math.pi / 2, "t": math.pi / 4, "tdg": -math.pi / 4}[op.name]
            ops.append(cirq.rz(theta).on(q[0]))
        elif op.name == "s":
            ops.append(cirq.S.on(q[0]))
        elif op.name == "sdg":
            ops.append(cirq.S.on(q[0]) ** -1)
        elif op.name == "t":
            ops.append(cirq.T.on(q[0]))
        elif op.name == "tdg":
            ops.append(cirq.T.on(q[0]) ** -1)
        elif op.name == "rx":
            ops.append(cirq.rx(op.params[0]).on(q[0]))
        elif op.name == "ry":
            ops.append(cirq.ry(op.params[0]).on(q[0]))
        elif op.name == "rz":
            ops.append(cirq.rz(op.params[0]).on(q[0]))
        elif op.name == "cx":
            ops.append(cirq.CNOT.on(q[0], q[1]))
        elif op.name == "cz":
            ops.append(cirq.CZ.on(q[0], q[1]))
        elif op.name == "swap":
            ops.append(cirq.SWAP.on(q[0], q[1]))
        elif with_channels:
            p = op.params[0]
            if op.name == "depol1":
                ops.append(cirq.depolarize(p=p, n_qubits=1).on(*q))
            elif op.name == "depol2":
                ops.append(cirq.depolarize(p=p, n_qubits=2).on(*q))
            elif op.name == "adamp":
                ops.append(cirq.amplitude_damp(gamma=p).on(q[0]))
            elif op.name == "bitflip":
                ops.append(cirq.bit_flip(p=p).on(q[0]))
        else:
            raise ValueError(f"unmapped channel {op.name}")
    return cirq.Circuit(ops), qubits


@register_backend
class CirqStatevector(BenchmarkBackend):
    name = "cirq_sv"
    label = "Cirq Simulator (NumPy)"
    import_name = "cirq"
    kind = "statevector"
    threads_mode = "env"
    max_qubits = 20
    homepage = "https://github.com/quantumlib/Cirq"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import cirq

        cc, qubits = build_cirq_circuit(circuit, with_channels=False)
        sim = cirq.Simulator(seed=seed)
        vec = sim.simulate(cc, qubit_order=qubits).final_state_vector
        return {"p_q0_1": prob_q0_1_from_statevector(vec, q0_is_lsb=False)}


@register_backend
class CirqDensity(BenchmarkBackend):
    name = "cirq_dm"
    label = "Cirq DensityMatrixSimulator"
    import_name = "cirq"
    kind = "density"
    threads_mode = "env"
    max_qubits = 12
    supports_channels = True
    homepage = "https://github.com/quantumlib/Cirq"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        import cirq

        cc, qubits = build_cirq_circuit(circuit, with_channels=True)
        sim = cirq.DensityMatrixSimulator(seed=seed)
        rho = sim.simulate(cc, qubit_order=qubits).final_density_matrix
        return {"p_q0_1": prob_q0_1_from_diag(rho, q0_is_lsb=False)}
