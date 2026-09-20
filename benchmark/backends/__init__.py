"""All backend adapters. Importing this package registers every backend."""

from __future__ import annotations

from benchmark.registry import BACKENDS


def _load_all() -> None:
    import importlib
    import pkgutil

    for mod in pkgutil.iter_modules(__path__):
        if mod.name not in ("base", "util"):
            importlib.import_module(f"{__name__}.{mod.name}")


_load_all()

__all__ = ["BACKENDS"]
