"""Backend adapter contract.

A backend wraps one simulator and executes :class:`~benchmark.ir.Circuit`
instances (gate list + optional inline channels).

Thread baselines
----------------
``threads_mode`` says how the *threads* dimension of the matrix is applied:

- ``"env"``    the runner exports OMP/BLAS thread limits in the worker
               subprocess before import (qulacs, lightning, quimb, cirq, qutip).
- ``"option"`` the backend takes a thread-count option at construction
               (aer, qsimcirq, qibo, uniqc — kernel threads via the global
               ``set_num_threads`` / ``set_parallel_enabled`` API).
- ``"batch"``  the kernel runs single-threaded, so "multi-thread" means
               running independent trajectory shots in parallel worker
               processes and measuring sampling *throughput*
               (uniqc statevector batch baseline).
- ``"none"``  the simulator is single-threaded with no knob.

Readout contract: ``run`` returns ``{"p_q0_1": float}`` — the probability of
measuring qubit 0 in state 1 (exact for ``shots == 0``, empirical otherwise).
Comparing a single scalar keeps timing free of output-format differences.
"""

from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from benchmark.ir import Circuit


class BenchmarkBackend(ABC):
    name: ClassVar[str]
    import_name: ClassVar[str | None] = None  # module required at runtime
    kind: ClassVar[str] = "statevector"  # statevector | density
    label: ClassVar[str] = ""  # human-readable (defaults to name)
    threads_mode: ClassVar[str] = "none"
    max_qubits: ClassVar[int] = 30
    supports_channels: ClassVar[bool] = False  # inline noise channels
    supports_shots: ClassVar[bool] = False  # shots > 0 sampling
    homepage: ClassVar[str] = ""

    def __init__(self, threads: int = 1) -> None:
        """Store the thread tier; ``option``-mode backends apply it now."""
        self.threads = threads
        if threads > 1:
            self.set_threads(threads)

    @classmethod
    def availability(cls) -> tuple[bool, str]:
        """``(available, reason)`` — checks that ``import_name`` is importable."""
        if cls.import_name is None:
            return True, ""
        if importlib.util.find_spec(cls.import_name) is None:
            return False, f"module '{cls.import_name}' not installed"
        return True, ""

    def set_threads(self, n: int) -> None:  # pragma: no cover - default no-op
        """Hook for ``threads_mode == "option"`` backends."""

    def supports(self, circuit: Circuit, shots: int) -> str | None:
        """Return a skip reason, or None when this backend can run the case."""
        if circuit.n_qubits > self.max_qubits:
            return f"n_qubits={circuit.n_qubits} > backend max {self.max_qubits}"
        if circuit.channels() and not self.supports_channels:
            return "backend does not support noise channels"
        if shots > 0 and not self.supports_shots:
            return "backend does not support shot sampling mode"
        if shots == 0 and self.threads_mode == "batch" and self.threads > 1:
            return "batch-parallel mode only applies to shot sampling"
        return None

    @abstractmethod
    def run(self, circuit: Circuit, shots: int, seed: int) -> dict:
        """Execute the circuit; return at least ``{"p_q0_1": float}``."""
        raise NotImplementedError
