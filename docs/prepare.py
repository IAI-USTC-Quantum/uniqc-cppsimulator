"""Copy repository markdown sources into the Sphinx source tree before a build.

Sphinx can only include documents that live inside its source directory, so
README.md / CHANGELOG.md / benchmark/README.md / doc/benchmark.md /
doc/benchmark/README_summary.md (plus the benchmark plots under
doc/benchmark/) are copied into ``docs/includes/`` -- git-ignored and
regenerated on every build, keeping a single source of truth.

Repo-relative links inside the copies are rewritten to point at the sibling
documents so every link resolves inside the built site. Run manually via
``python docs/prepare.py``; conf.py also invokes it automatically, so
``sphinx-build`` alone is enough.

Usage:
    python docs/prepare.py [--check]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
ROOT = DOCS_DIR.parent
INCLUDES = DOCS_DIR / "includes"

GH_REPO = "https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator"

# (source, destination, {old substring: new substring})
COPIES: list[tuple[Path, Path, dict[str, str]]] = [
    (
        ROOT / "README.md",
        INCLUDES / "readme.md",
        {
            # Sibling documents inside docs/includes/
            "](doc/benchmark.md)": "](benchmark-results.md)",
            "](doc/benchmark/README_summary.md)": "](benchmark-summary.md)",
            "](benchmark/README.md)": "](benchmark-methodology.md)",
            "](CHANGELOG.md)": "](changelog.md)",
            # Repo files that are not part of the site -> absolute GitHub links
            "](docs/)": f"]({GH_REPO}/tree/main/docs)",
            "](uniqc_cpp.pyi)": f"]({GH_REPO}/blob/main/uniqc_cpp.pyi)",
            "](LICENSE)": f"]({GH_REPO}/blob/main/LICENSE)",
        },
    ),
    (
        ROOT / "CHANGELOG.md",
        INCLUDES / "changelog.md",
        {
            "](README.md#性能基准)": "](readme.md#性能基准)",
            "](doc/benchmark.md)": "](benchmark-results.md)",
            "](benchmark/README.md)": "](benchmark-methodology.md)",
        },
    ),
    (
        ROOT / "benchmark" / "README.md",
        INCLUDES / "benchmark-methodology.md",
        {
            "](../README.md#性能基准)": "](readme.md#性能基准)",
            "](../doc/benchmark.md)": "](benchmark-results.md)",
            "](../doc/benchmark/README_summary.md)": "](benchmark-summary.md)",
        },
    ),
    (
        ROOT / "doc" / "benchmark.md",
        INCLUDES / "benchmark-results.md",
        {
            "](../benchmark/README.md)": "](benchmark-methodology.md)",
            "](../README.md#性能基准)": "](readme.md#性能基准)",
            "](benchmark/README_summary.md)": "](benchmark-summary.md)",
            # benchmark/*.png image links stay relative; the plots are copied
            # to includes/benchmark/ below so they resolve as-is.
        },
    ),
    (
        ROOT / "doc" / "benchmark" / "README_summary.md",
        INCLUDES / "benchmark-summary.md",
        {
            "](doc/benchmark.md)": "](benchmark-results.md)",
            "](../../benchmark/README.md)": "](benchmark-methodology.md)",
            "](../../README.md#性能基准)": "](readme.md#性能基准)",
            "](../../README.md#快速上手)": "](readme.md#快速上手)",
        },
    ),
]

# (source directory, glob, destination directory)
ASSET_COPIES: list[tuple[Path, str, Path]] = [
    (ROOT / "doc" / "benchmark", "*.png", INCLUDES / "benchmark"),
]


def prepare(check: bool = False) -> list[str]:
    """Perform the copies; return a list of written file names (for output)."""
    written: list[str] = []
    for src, dst, replacements in COPIES:
        if not src.is_file():
            raise FileNotFoundError(f"missing documentation source: {src}")
        text = src.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        if not check or not dst.is_file() or dst.read_text(encoding="utf-8") != text:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8", newline="\n")
        written.append(str(dst.relative_to(DOCS_DIR)))
    for src_dir, pattern, dst_dir in ASSET_COPIES:
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_dir.glob(pattern)):
            dst = dst_dir / src.name
            if not check or not dst.is_file() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)
            written.append(str(dst.relative_to(DOCS_DIR)))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the generated files are missing or stale (CI guard)",
    )
    args = parser.parse_args(argv)
    try:
        written = prepare(check=args.check)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"prepared {len(written)} files under docs/includes/:")
    for name in written:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
