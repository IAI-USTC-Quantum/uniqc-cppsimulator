"""Registry of extension points: circuit families, noise presets, backends.

Adding a new circuit family = decorate a builder with ``@register_circuit``.
Adding a noise preset = ``@register_noise``.  Adding a simulator = subclass
``BenchmarkBackend`` and put the module in ``benchmark/backends/``; importing
``benchmark.backends`` registers it automatically.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from benchmark.backends.base import BenchmarkBackend
    from benchmark.ir import Circuit, NoisePreset

CircuitBuilder = Callable[[int, int, int], "Circuit"]  # (n_qubits, depth, seed)

CIRCUITS: dict[str, CircuitBuilder] = {}
NOISE: dict[str, NoisePreset] = {}
BACKENDS: dict[str, type[BenchmarkBackend]] = {}


def register_circuit(name: str) -> Callable[[CircuitBuilder], CircuitBuilder]:
    def deco(fn: CircuitBuilder) -> CircuitBuilder:
        if name in CIRCUITS:
            raise ValueError(f"duplicate circuit family {name!r}")
        CIRCUITS[name] = fn
        return fn

    return deco


def register_noise(preset: NoisePreset) -> NoisePreset:
    if preset.name in NOISE:
        raise ValueError(f"duplicate noise preset {preset.name!r}")
    NOISE[preset.name] = preset
    return preset


def register_backend(cls: type[BenchmarkBackend]) -> type[BenchmarkBackend]:
    if cls.name in BACKENDS:
        raise ValueError(f"duplicate backend {cls.name!r}")
    BACKENDS[cls.name] = cls
    return cls
