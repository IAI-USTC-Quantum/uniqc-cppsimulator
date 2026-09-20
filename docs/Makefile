# Minimal makefile for Sphinx documentation.
#
# Usage (from docs/):
#     make html PYTHON=../.venv-bench/bin/python

PYTHON ?= python

SPHINXPROJ    = uniqc-cppsimulator
SOURCEDIR     = .
BUILDDIR      = _build
SPHINXBUILD   = $(PYTHON) -m sphinx

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
