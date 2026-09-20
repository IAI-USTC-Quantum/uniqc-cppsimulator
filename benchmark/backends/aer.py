"""Qiskit Aer adapters (statevector / density_matrix methods).

Noise channels are appended inline as ``QuantumError`` instructions, mirroring
the IR semantics one-to-one (Aer samples a trajectory per op on the
statevector method, applies the superoperator on density_matrix).
"""

from __future__ import annotations

from benchmark.backends.base import BenchmarkBackend
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def _noise_instruction(op):
    from qiskit_aer.noise import amplitude_damping_error, depolarizing_error, pauli_error

    if op.name == "depol1":
        return depolarizing_error(op.params[0], 1).to_instruction()
    if op.name == "depol2":
        return depolarizing_error(op.params[0], 2).to_instruction()
    if op.name == "adamp":
        return amplitude_damping_error(op.params[0]).to_instruction()
    if op.name == "bitflip":
        return pauli_error([("X", op.params[0]), ("I", 1 - op.params[0])]).to_instruction()
    return None  # pragma: no cover


def build_qiskit_circuit(circuit: Circuit, n_clbits: int = 0):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(circuit.n_qubits, n_clbits)
    for op in circuit.ops:
        q = op.qubits
        if op.name == "h":
            qc.h(q[0])
        elif op.name == "x":
            qc.x(q[0])
        elif op.name == "y":
            qc.y(q[0])
        elif op.name == "z":
            qc.z(q[0])
        elif op.name == "s":
            qc.s(q[0])
        elif op.name == "sdg":
            qc.sdg(q[0])
        elif op.name == "t":
            qc.t(q[0])
        elif op.name == "tdg":
            qc.tdg(q[0])
        elif op.name in ("rx", "ry", "rz"):
            getattr(qc, op.name)(op.params[0], q[0])
        elif op.name == "cx":
            qc.cx(q[0], q[1])
        elif op.name == "cz":
            qc.cz(q[0], q[1])
        elif op.name == "swap":
            qc.swap(q[0], q[1])
        else:
            qc.append(_noise_instruction(op), list(q))
    return qc


def _counts_p_q0_1(counts: dict, shots: int) -> float:
    # Qiskit count keys are big-endian printed strings: qubit 0 is the last char.
    ones = sum(n for bits, n in counts.items() if bits.replace(" ", "")[-1] == "1")
    return ones / shots


class _AerBase(BenchmarkBackend):
    import_name = "qiskit_aer"
    threads_mode = "option"
    supports_channels = True
    supports_shots = True
    homepage = "https://github.com/Qiskit/qiskit-aer"
    method = "statevector"

    def __init__(self, threads: int = 1) -> None:
        super().__init__(threads)
        from qiskit_aer import AerSimulator

        self._sim = AerSimulator(
            method=self.method,
            max_parallel_threads=threads,
            max_parallel_experiments=1,
        )

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        qc = build_qiskit_circuit(circuit, n_clbits=1 if shots else 0)
        if shots == 0:
            qc.save_probabilities(qubits=[0])
            result = self._sim.run(qc, shots=1, seed_simulator=seed).result()
            probs = result.data(0)["probabilities"]
            return {"p_q0_1": float(probs[1])}
        qc.measure(0, 0)  # counts readout for qubit 0
        result = self._sim.run(qc, shots=shots, seed_simulator=seed).result()
        return {"p_q0_1": _counts_p_q0_1(result.get_counts(), shots)}


@register_backend
class AerStatevector(_AerBase):
    name = "aer_sv"
    label = "Qiskit Aer statevector"
    kind = "statevector"
    method = "statevector"


@register_backend
class AerDensity(_AerBase):
    name = "aer_dm"
    label = "Qiskit Aer density_matrix"
    kind = "density"
    method = "density_matrix"
    max_qubits = 15
