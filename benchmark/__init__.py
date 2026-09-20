"""uniqc-cppsimulator cross-simulator CPU benchmark suite.

Importing this package registers every circuit family, noise preset and
backend adapter (registration happens at import of the sibling modules).
"""

from benchmark import circuits, noise  # noqa: F401  registration side effect

__version__ = "0.1.0"
