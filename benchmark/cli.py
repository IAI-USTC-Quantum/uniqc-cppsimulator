"""Command-line interface: python -m benchmark <subcommand> ..."""

from __future__ import annotations

import argparse
import json
import sys

from benchmark import plotting, report, runner
from benchmark.backends import BACKENDS
from benchmark.presets import PRESETS
from benchmark.registry import CIRCUITS, NOISE


def cmd_list(args: argparse.Namespace) -> None:
    """Print registered backends (with availability), circuits, noise and presets."""
    if args.section in ("backends", "all"):
        print("backends:")
        for name, cls in sorted(BACKENDS.items()):
            ok, reason = cls.availability()
            flag = "ok" if ok else f"missing ({reason})"
            print(f"  {name:<14} {cls.kind:<12} threads={cls.threads_mode:<7} "
                  f"max_q={cls.max_qubits:<3} {flag}")
    if args.section in ("circuits", "all"):
        print("circuits:", ", ".join(sorted(CIRCUITS)))
    if args.section in ("noise", "all"):
        print("noise presets:")
        for name, preset in sorted(NOISE.items()):
            print(f"  {name:<14} kind={preset.kind} p1={preset.p1} p2={preset.p2} gamma={preset.gamma}")
    if args.section in ("presets", "all"):
        print("presets:", ", ".join(sorted(PRESETS)))


def cmd_selftest(args: argparse.Namespace) -> None:
    """Run the known-answer check for the requested (or all) backends."""
    names = args.backends.split(",") if args.backends else sorted(BACKENDS)
    results = runner.selftest_backends(names)
    failed = []
    for name, res in results.items():
        status = res.get("selftest", res.get("status", "?"))
        print(f"{name:<14} {status}")
        if status != "pass":
            failed.append(name)
            for line in json.dumps(res, ensure_ascii=False).splitlines():
                print(f"    {line[:160]}")
    if failed:
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> None:
    """Execute a preset matrix (see ``runner.run_matrix``)."""
    selected = args.backends.split(",") if args.backends else None
    runner.run_matrix(
        preset_name=args.preset,
        out_path=args.out,
        selected_backends=selected,
        limit=args.limit,
        resume=args.resume,
    )


def cmd_plot(args: argparse.Namespace) -> None:
    """Render every registered figure from a results JSON."""
    figures = plotting.plot_all(args.results, args.out_dir)
    for fig, path in figures:
        print(f"wrote {path}")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate ``doc/benchmark.md`` and the README summary include."""
    with open(args.results, encoding="utf-8") as fh:
        data = json.load(fh)
    doc = report.write_report(data, args.doc_dir)
    summary = report.write_readme_summary(data, doc)
    print(f"wrote {doc}")
    print(f"wrote {summary}")


def build_parser() -> argparse.ArgumentParser:
    """Argument parser for ``python -m benchmark <command>``."""
    parser = argparse.ArgumentParser(prog="benchmark", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list registered backends/circuits/noise/presets")
    p_list.add_argument("--section", default="all",
                        choices=["all", "backends", "circuits", "noise", "presets"])
    p_list.set_defaults(func=cmd_list)

    p_st = sub.add_parser("selftest", help="known-answer check for adapter wiring")
    p_st.add_argument("--backends", help="comma-separated subset")
    p_st.set_defaults(func=cmd_selftest)

    p_run = sub.add_parser("run", help="run a benchmark preset")
    p_run.add_argument("--preset", default="smoke", choices=sorted(PRESETS))
    p_run.add_argument("--out", default="benchmark/results.json")
    p_run.add_argument("--backends", help="comma-separated subset")
    p_run.add_argument("--limit", type=int, help="run only the first N cases")
    p_run.add_argument("--resume", action="store_true",
                       help="reuse completed cases from --out if present")
    p_run.set_defaults(func=cmd_run)

    p_plot = sub.add_parser("plot", help="render charts from a results JSON")
    p_plot.add_argument("--results", default="benchmark/results.json")
    p_plot.add_argument("--out-dir", default="doc/benchmark")
    p_plot.set_defaults(func=cmd_plot)

    p_rep = sub.add_parser("report", help="generate doc/benchmark.md and README summary")
    p_rep.add_argument("--results", default="benchmark/results.json")
    p_rep.add_argument("--doc-dir", default="doc")
    p_rep.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
