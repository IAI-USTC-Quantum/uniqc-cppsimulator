"""uniqc_cpp DensityOperatorSimulator adapter (deterministic noise, <= 10q)."""

from __future__ import annotations

import uniqc_cpp
from benchmark.backends.base import BenchmarkBackend
from benchmark.backends.uniqc_sv import _apply_ops
from benchmark.ir import Circuit
from benchmark.registry import register_backend


@register_backend
class UniqcDensity(BenchmarkBackend):
    name = "uniqc_dm"
    label = "uniqc_cpp DensityOperatorSimulator"
    import_name = "uniqc_cpp"
    kind = "density"
    threads_mode = "none"
    max_qubits = 10
    supports_channels = True
    homepage = "https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator"

    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        sim = uniqc_cpp.DensityOperatorSimulator()
        sim.init_n_qubit(circuit.n_qubits)
        _apply_ops(sim, circuit.ops)
        return {"p_q0_1": sim.pmeasure(0)[1]}
