"""Noise presets. Applied by ``ir.apply_noise`` as inline channel ops."""

from __future__ import annotations

from benchmark.ir import NoisePreset
from benchmark.registry import register_noise

register_noise(NoisePreset("none", kind="none"))
register_noise(NoisePreset("depol", kind="depolarizing", p1=0.001, p2=0.01))
register_noise(NoisePreset("depol-strong", kind="depolarizing", p1=0.01, p2=0.05))
register_noise(NoisePreset("adamp", kind="amplitude_damping", gamma=0.01))
register_noise(NoisePreset("bitflip", kind="bitflip", p1=0.005))
