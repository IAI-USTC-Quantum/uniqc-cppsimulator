# Sphinx configuration for the uniqc-cppsimulator documentation.
#
# Build (from the repository root, with a venv that has the extension and
# sphinx installed):
#     .venv-bench/bin/python -m sphinx -b html docs docs/_build/html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "uniqc-cppsimulator"
copyright = "2026, Agony"
author = "Agony"

try:
    from importlib.metadata import version as _dist_version

    release = _dist_version("uniqc-cppsimulator")
except Exception:  # noqa: BLE001 - docs build fine without an installed dist
    release = "unknown"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
add_module_names = True

html_theme = "alabaster"
html_title = "uniqc-cppsimulator"

# The benchmark package is pure Python, but importing it pulls in the
# uniqc_cpp extension; both are available in the documented environment.
suppress_warnings: list[str] = []
