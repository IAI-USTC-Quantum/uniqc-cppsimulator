"""Markdown report generation from a results JSON.

``write_report`` produces the detailed ``doc/benchmark.md``; ``write_readme_summary``
produces a compact include-file for the README section.
"""

from __future__ import annotations

import os

from benchmark.backends import BACKENDS


def _label(backend: str) -> str:
    return BACKENDS[backend].label if backend in BACKENDS else backend


def _fmt_ms(ms: float) -> str:
    """Human-friendly milliseconds ("2.13 s", "13 ms", "0.42 ms")."""
    if ms >= 1000:
        return f"{ms / 1000:.2f} s"
    if ms >= 10:
        return f"{ms:.0f} ms"
    return f"{ms:.2f} ms"


def _ok(results: list[dict]) -> list[dict]:
    """Only successfully measured records."""
    return [r for r in results if r.get("status") == "ok"]


def _pivot_table(rows: list[dict], title: str) -> str:
    """rows: one per (backend, circuit, qubits, threads) with stats."""
    if not rows:
        return f"### {title}\n\n_(no data)_\n"
    circuits = sorted({(r["circuit"], r.get("depth", 1)) for r in rows})
    qubits = sorted({r["n_qubits"] for r in rows})
    threads_list = sorted({r["threads"] for r in rows})
    backends = sorted({r["backend"] for r in rows},
                      key=lambda b: (not b.startswith("uniqc"), b))
    parts = [f"### {title}\n"]
    for threads in threads_list:
        parts.append(f"\n#### threads = {threads}\n")
        header = ["backend"] + [f"{c}(d{d}) n={q}" for c, d in circuits for q in qubits]
        parts.append("| " + " | ".join(header) + " |")
        parts.append("|" + "---|" * len(header))
        for backend in backends:
            cells = [_label(backend)]
            for circuit, depth in circuits:
                for q in qubits:
                    r = next((r for r in rows if r["backend"] == backend
                              and r["circuit"] == circuit and r["n_qubits"] == q
                              and r["threads"] == threads), None)
                    if r is None:
                        cells.append("—")
                        continue
                    med = r["stats"]["median_ms"]
                    cell = _fmt_ms(med)
                    best = _is_best(rows, circuit, depth, q, threads)
                    if best == backend:
                        cell = f"**{cell}**"
                    cells.append(cell)
            parts.append("| " + " | ".join(cells) + " |")
    return "\n".join(parts) + "\n"


def _is_best(rows, circuit, depth, q, threads) -> str | None:
    """Backend name with the lowest median for this (circuit, qubits,
    threads) point, or None when there is nothing to compare."""
    candidates = [r for r in rows if r["circuit"] == circuit and r["depth"] == depth
                  and r["n_qubits"] == q and r["threads"] == threads]
    if not candidates:
        return None
    return min(candidates, key=lambda r: r["stats"]["median_ms"])["backend"]


def _meta_table(meta: dict) -> str:
    """Markdown tables for the run environment and per-backend versions."""
    backends = meta.get("backends", {})
    lines = [
        "| field | value |",
        "|---|---|",
        f"| 时间 | {meta.get('timestamp')} |",
        f"| 主机 | {meta.get('hostname')} |",
        f"| CPU | {meta.get('cpu')} × {meta.get('cores')} cores |",
        f"| 内存 | {meta.get('memory')} |",
        f"| Python | {meta.get('python')} |",
        f"| 平台 | {meta.get('platform')} |",
        "",
        "**模拟器版本**",
        "",
        "| backend | version | selftest |",
        "|---|---|---|",
    ]
    selftests = meta.get("selftest", {})
    for name, info in sorted(backends.items()):
        version = info.get("version") or "?"
        st = selftests.get(name, {})
        flag = {"pass": "✅", "fail": "❌"}.get(st.get("selftest", ""), "—")
        if not info.get("available"):
            version = f"未安装 ({info.get('reason', '')})"
        lines.append(f"| {_label(name)} | {version} | {flag} |")
    return "\n".join(lines)


def write_report(data: dict, doc_dir: str) -> str:
    os.makedirs(doc_dir, exist_ok=True)
    meta, results = data["meta"], data["results"]
    dropped = data.get("dropped", {})
    ok = _ok(results)
    ideal = [r for r in ok if r.get("group") == "ideal-sv"]
    noise = [r for r in ok if str(r.get("group", "")).startswith("noise-dm")]
    sampling = [r for r in ok if r.get("group") == "sampling"]

    uniqc_version = (meta.get("backends", {}).get("uniqc_sv", {}) or {}).get("version") or "?"
    notes = [
        "## 注意事项",
        "",
        f"- 本轮 uniqc_cpp 版本 `{uniqc_version}`。",
        (
            "- **历史 release bug（源码已修复）**：`StatevectorSimulator.measure_single_shot(int)` 标量重载在 1.0.1 及更早 release 中会无限递归死循环"
            "（`{ qubit }` 花括号初始化在重载决议中选中标量重载自身，尾递归被优化为循环）。"
            "list 重载不受影响，采样适配器统一使用 `measure_single_shot([0])` 规避。"
        ),
        "- 线程维度机制不同：外部模拟器与 uniqc_sv 均为内核内门级并行（OMP/选项/`set_num_threads`）；uniqc_sv_batch 为**进程池 shot 级并行**（采样吞吐），与门级并行的数值不可直接互比。",
        "- 基准未做绑核/独占机器等公平性控制（共享开发机），结果反映相对趋势。",
    ]
    if dropped:
        notes.append("- 未参与对比：" + "; ".join(f"`{k}` — {v}" for k, v in sorted(dropped.items())))

    md = [
        "# Benchmark 详情",
        "",
        "本页由 `python -m benchmark report` 生成；方法论、矩阵定义与扩展方法见",
        "[benchmark/README.md](../benchmark/README.md)，摘要见[仓库 README](../README.md#性能基准)。",
        "",
        "## 运行环境",
        "",
        _meta_table(meta),
    ]
    if dropped:
        md += ["", "**未参与对比的后端**：" + ", ".join(
            f"`{k}` ({v})" for k, v in sorted(dropped.items()))]

    md += ["", "## 理想态矢量模拟（无噪声，读出精确概率）", "",
           _pivot_table(ideal, "ideal statevector — median wall time")]
    md += ["", "## 噪声密度矩阵模拟", "",
           _pivot_table(noise, "density matrix — median wall time")]
    if sampling:
        md += ["", "## 轨迹采样（shots 模式）", "",
               "| backend | qubits | shots | threads | median time | shots/s |",
               "|---|---|---|---|---|---|"]
        for r in sorted(sampling, key=lambda r: (r["backend"], r["n_qubits"], r["threads"])):
            med = r["stats"]["median_ms"]
            md.append(f"| {_label(r['backend'])} | {r['n_qubits']} | {r['shots']} | "
                      f"{r['threads']} | {_fmt_ms(med)} | {r['shots'] / (med / 1e3):,.0f} |")

    md += [
        "",
        "## 图表",
        "",
        "![ideal runtime](benchmark/ideal_runtime_vs_qubits.png)",
        "",
        "![thread speedup](benchmark/thread_speedup.png)",
        "",
        "![noise runtime](benchmark/noise_runtime_vs_qubits.png)",
        "",
        "![sampling throughput](benchmark/sampling_throughput.png)",
        "",
        "## 结果 JSON",
        "",
        (
            "原始数据（含每次重复的耗时、RSS、p_q0_1）：`benchmark/results.json`（运行时由 "
            "`--out` 指定，仓库内快照见 `doc/benchmark/results-<date>.json`）。"
        ),
        "",
        *notes,
    ]
    path = os.path.join(doc_dir, "benchmark.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    return path


def write_readme_summary(data: dict, doc_path: str) -> str:
    """Compact summary tables included by the README benchmark section."""
    ok = _ok(data["results"])
    meta = data["meta"]
    # headline table compares single-thread runs (uniqc_sv also has
    # multi-thread data now — see the speedup figure — but the like-for-like
    # cross-simulator table stays at threads=1).
    threads = 1
    lines = [
        (
            f"运行环境：{meta.get('cpu')}（{meta.get('cores')} 核），Python {meta.get('python')}，"
            f"threads=1；完整环境与版本表见[详情文档](doc/benchmark.md)。"
        ),
        "",
        "| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |",
        "|---|---|---|---|---|",
    ]
    ideal = [r for r in ok if r.get("group") == "ideal-sv" and r["threads"] == threads]
    for circuit in sorted({r["circuit"] for r in ideal}):
        rows = [r for r in ideal if r["circuit"] == circuit]
        uniqc_ns = {r["n_qubits"] for r in rows if r["backend"] == "uniqc_sv"}
        other_ns = {r["n_qubits"] for r in rows if r["backend"] != "uniqc_sv"}
        inter = uniqc_ns & other_ns
        if not inter:
            continue
        n = max(inter)
        at_n = [r for r in rows if r["n_qubits"] == n]
        best = min(at_n, key=lambda r: r["stats"]["median_ms"])
        uniqc = next((r for r in at_n if r["backend"] == "uniqc_sv"), None)
        ratio = f"×{uniqc['stats']['median_ms'] / best['stats']['median_ms']:.1f}" if uniqc else "—"
        uniqc_s = _fmt_ms(uniqc["stats"]["median_ms"]) if uniqc else "—"
        lines.append(f"| {circuit} | {n} | {_label(best['backend'])} "
                     f"({_fmt_ms(best['stats']['median_ms'])}) | {uniqc_s} | {ratio} |")
    path = os.path.join(os.path.dirname(doc_path), "benchmark", "README_summary.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path
