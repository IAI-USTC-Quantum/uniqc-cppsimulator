"""uniqc_cpp StatevectorSimulator adapter.

The C++ kernel is single-threaded per simulation and the pybind11 bindings
hold the GIL, so ``threads_mode == "batch"``: the multi-thread baseline runs
independent trajectory shots in parallel worker processes (multiprocessing)
and measures sampling throughput.  Noise channels are stochastic on the
statevector (quantum-trajectory Monte Carlo), one trajectory per shot.
"""

from __future__ import annotations

import concurrent.futures

import uniqc_cpp
from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.util import prob_q0_1_from_statevector
from benchmark.ir import Circuit
from benchmark.registry import register_backend


def _apply_ops(sim, ops) -> None:
    """Apply IR ops (gates + channels) to a uniqc simulator object.

    Works for both simulator classes: they share the same Python API for
    gates, and the noise channels are stochastic on the statevector but
    deterministic superoperators on the density operator.
    """
    for op in ops:
        name, q = op.name, op.qubits
        if name == "h":
            sim.hadamard(q[0])
        elif name == "x":
            sim.x(q[0])
        elif name == "y":
            sim.y(q[0])
        elif name == "z":
            sim.z(q[0])
        elif name == "s":
            sim.s(q[0])
        elif name == "sdg":
            sim.s(q[0], dagger=True)
        elif name == "t":
            sim.t(q[0])
        elif name == "tdg":
            sim.t(q[0], dagger=True)
        elif name in ("rx", "ry", "rz"):
            getattr(sim, name)(q[0], op.params[0])
        elif name == "cx":
            sim.cnot(q[0], q[1])
        elif name == "cz":
            sim.cz(q[0], q[1])
        elif name == "swap":
            sim.swap(q[0], q[1])
        elif name == "depol1":
            sim.depolarizing(q[0], op.params[0])
        elif name == "depol2":
            sim.twoqubit_depolarizing(q[0], q[1], op.params[0])
        elif name == "adamp":
            sim.amplitude_damping(q[0], op.params[0])
        elif name == "bitflip":
            sim.bitflip(q[0], op.params[0])
        else:  # pragma: no cover
            raise ValueError(f"unmapped op {name}")


def _trajectory_shots(payload: tuple) -> int:
    """Worker: run ``n_shots`` stochastic trajectories, return # of 1-outcomes."""
    ops, n_qubits, n_shots, seed = payload
    uniqc_cpp.seed(seed)
    ones = 0
    for _ in range(n_shots):
        sim = uniqc_cpp.StatevectorSimulator()
        sim.init_n_qubit(n_qubits)
        _apply_ops(sim, ops)
        # list overload: the scalar overload of measure_single_shot recurses
        # into itself (braced-init-list resolves to the size_t overload) and
        # dead-loops in every released wheel incl. 1.0.1 — see doc notes
        ones += sim.measure_single_shot([0])
    return ones


@register_backend
class UniqcStatevector(BenchmarkBackend):
    name = "uniqc_sv"
    label = "uniqc_cpp StatevectorSimulator"
    import_name = "uniqc_cpp"
    kind = "statevector"
    threads_mode = "batch"
    max_qubits = 30
    supports_channels = True
    supports_shots = True
    homepage = "https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        ops = circuit.ops
        if shots == 0:
            sim = uniqc_cpp.StatevectorSimulator()
            sim.init_n_qubit(circuit.n_qubits)
            _apply_ops(sim, ops)
            if circuit.n_qubits <= 22:  # avoid copying >4M-amplitude vectors
                p = prob_q0_1_from_statevector(sim.state)
            else:
                p = sim.pmeasure(0)[1]
            return {"p_q0_1": p}

        workers = max(1, self.threads)
        per = shots // workers
        if workers == 1 or per == 0:
            ones = _trajectory_shots((ops, circuit.n_qubits, shots, seed))
            return {"p_q0_1": ones / shots}

        base = (seed * 1000003 + 7919) & 0xFFFFFFFF  # C++ seed() takes 32-bit
        payloads = [
            (ops, circuit.n_qubits, per, (base + i * 104729) & 0xFFFFFFFF)
            for i in range(workers)
        ]
        remainder = shots - per * workers
        ctx = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
        with ctx as pool:
            ones = sum(pool.map(_trajectory_shots, payloads))
        if remainder:  # pragma: no cover - matrix uses divisible shot counts
            ones += _trajectory_shots((ops, circuit.n_qubits, remainder, (base + workers) & 0xFFFFFFFF))
        return {"p_q0_1": ones / shots}
