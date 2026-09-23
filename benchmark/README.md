# Benchmark 套件

跨模拟器 CPU 性能基准：以 `uniqc_cpp`（Statevector / DensityOperator）为对象，与主流
pip 可装 CPU 模拟器对比，覆盖**单线程 vs 多线程**基线、**多线路族 × 多 qubit 数**、
**多噪声模型**。结果摘要进[仓库 README](../README.md#性能基准)，完整数据与图表在
[doc/benchmark.md](../doc/benchmark.md)。

## 快速开始

```bash
uv venv .venv-bench --python 3.12
uv pip install --python .venv-bench/bin/python uniqc-cppsimulator \
    matplotlib qiskit qiskit-aer cirq qsimcirq qulacs pennylane pennylane-lightning \
    qibo qibojit quimb qutip qutip-qip amazon-braket-sdk   # 按需安装对比对象
.venv-bench/bin/python -m benchmark list          # 看已注册后端/线路/噪声/预设
.venv-bench/bin/python -m benchmark selftest      # 适配器正确性（已知答案）检查
.venv-bench/bin/python -m benchmark run --preset smoke   # ~2 分钟冒烟
.venv-bench/bin/python -m benchmark run --preset standard --out benchmark/results.json
.venv-bench/bin/python -m benchmark plot    --results benchmark/results.json
.venv-bench/bin/python -m benchmark report  --results benchmark/results.json
```

基准对象默认是 PyPI 最新 release 的 `uniqc-cppsimulator`（对比其余模拟器同样取安装时的最新版），
版本会随结果 JSON 一并记录。

未安装的模拟器自动跳过并记录原因；`--backends a,b`、`--limit N`、`--resume`
可缩小/续跑矩阵。

## 测什么

| 维度 | 取值 | 说明 |
|---|---|---|
| 线路族 | `ghz`, `qft`, `random`(分层随机), `qaoa` | 由 `benchmark/circuits.py` 注册，按 `(n_qubits, depth, seed)` 参数化 |
| qubit 数 | 4 → 26（standard） | 每个后端有各自上限（如密度矩阵 10–15q） |
| 噪声 | `none`, `depol`, `depol-strong`, `adamp`, `bitflip` | 以内联通道算子插入门后（`benchmark/noise.py` + `ir.apply_noise`） |
| shots | 0（精确概率）或 1024（轨迹采样） | 采样模式衡量含噪线路的 shots 吞吐 |
| 线程 | 1 vs N（`presets.DEFAULT_THREADS`） | 见下 |

指标：warm-up 1 次 + N 次重复的**墙钟时间**（median/mean/min/std，ms）、峰值 RSS、
读出量统一为标量 `P(q0=1)`（避免各后端输出格式差异污染计时）。

## 单线程 vs 多线程基线

各后端拿到 `threads` 参数的方式（`BenchmarkBackend.threads_mode`）：

- `option` — 后端原生线程选项：Aer `max_parallel_threads`、qsim `QSimOptions(cpu_threads)`、qibo `set_threads`、uniqc `set_num_threads` + `set_parallel_enabled`（内核门级并行）
- `env` — 线程数由 runner 在 worker 子进程 import 前通过 `OMP_NUM_THREADS` 等固定：qulacs、lightning、quimb、cirq、qutip、braket
- `batch` — **uniqc_sv_batch 专属**：轨迹在单线程内核上由 `ProcessPoolExecutor` 并行跑独立 shots，测**采样吞吐**（等价于 shot-parallelism）
- `none` — 单线程内核无旋钮

> 注意：`batch` 与 `option`/`env` 的并行机制不同（任务级并行 vs 门级并行），
> 两者数字不可直接互比——这正是图表分开展示的原因。

## 方法论

- 每个 case 在**独立子进程**中执行（`python -m benchmark.worker --case-json ...`），
  避免线程环境变量与 JIT/缓存串扰；runner 串行调度保证计时隔离。
- 每个 case 超时（smoke 180s / standard 300s+）则记 `timeout` 并继续。
- 运行前对每个后端跑 4 条已知答案微线路（`worker._reference_cases`），
  校验门映射与比特序；未通过的后端被排除出结果。
- 基准忽略整机公平性（共享机器、未绑核），结果用于相对趋势而非论文级数值。

## 如何扩展

| 想加什么 | 做什么 |
|---|---|
| 新线路族 | `benchmark/circuits.py` 里实现 `builder(n, depth, seed) -> Circuit` 并 `@register_circuit("name")` |
| 新噪声 | `benchmark/noise.py` 加 `NoisePreset`（通道算子由 `ir.apply_noise` 统一插入） |
| 新模拟器 | `benchmark/backends/` 新建模块，继承 `BenchmarkBackend`，实现 `run()` 把 IR 翻译成本地 API，加 `@register_backend` |
| 新矩阵 | `benchmark/presets.py` 加 `Group` / `PRESETS` 条目 |
| 新图表 | `benchmark/plotting.py` 实现 `fig_xxx(data, out_dir)` 并 `@plotter` |

新后端只需支持 IR 里的门子集（h/x/y/z/s/sdg/t/tdg/rx/ry/rz/cx/cz/swap）；
噪声通道 (`depol1/depol2/adamp/bitflip`) 是可选能力（`supports_channels`），
矩阵会自动跳过不支持的后端。
