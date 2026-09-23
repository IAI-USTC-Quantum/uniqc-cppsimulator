# uniqc-cppsimulator

UnifiedQuantum 的 C++ 量子线路模拟内核，独立发版。

*The native C++ simulation kernel of [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum), published as a standalone package.*

## 定位

本仓库提供两个高性能 C++ 模拟器，通过 pybind11 暴露为 **`uniqc_cpp`** Python 扩展模块：

- `StatevectorSimulator` — 态矢量模拟器（最多 30 量子比特）
- `DensityOperatorSimulator` — 密度算符模拟器（最多 10 量子比特，支持噪声通道）

它原来是 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 仓库的 `UniqcCpp/` 目录，自 v0.0.18 起拆分为独立仓库、独立版本、独立发布。UnifiedQuantum 通过 PyPI 依赖本包，二者接口保持兼容。

**安装本包后，import 名为 `uniqc_cpp`**（分发名 `uniqc-cppsimulator`，import 名 `uniqc_cpp`）。

## 安装

```bash
pip install uniqc-cppsimulator
```

提供 Linux / Windows / macOS 的 cp310–cp314 预编译 wheel；其余平台自动从 sdist 源码编译，需要满足下方"源码构建要求"。

## 快速上手

```python
import uniqc_cpp

sim = uniqc_cpp.StatevectorSimulator()
sim.init_n_qubit(2)
sim.hadamard(0)
sim.cnot(0, 1)
print(sim.pmeasure([0, 1]))  # Bell 态: [0.5, 0, 0, 0.5]
```

完整 API 见仓库根目录的类型存根 [`uniqc_cpp.pyi`](uniqc_cpp.pyi)（安装后随扩展一起发布，IDE / 类型检查器可直接使用）。

## 源码构建要求

- CMake >= 3.22
- 支持 C++17 的编译器（MSVC / gcc / clang）
- pybind11（构建隔离模式下由 `pyproject.toml` 自动提供）
- 第三方库 [fmt](https://fmt.dev/) 已 vendored 在 `UniqcCpp/Thirdparty/`，无需额外安装

```bash
git clone https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator.git
cd uniqc-cppsimulator
pip install .
```

## 测试

```bash
# Python 绑定测试
pytest tests/

# C++ 原生测试
cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release \
  -Dpybind11_DIR="$(python -c 'import pybind11; print(pybind11.get_cmake_dir())')"
cmake --build build-cpp --config Release
./build-cpp/bin/Release/UnifiedQuantumTest   # Windows: .\build-cpp\bin\Release\UnifiedQuantumTest.exe
```

## 文档

Sphinx 文档（安装/构建、基准套件使用、`benchmark` 包 API 参考、`uniqc_cpp` 扩展 API 参考）位于 [`docs/`](docs/)：

```bash
uv pip install --python .venv-bench/bin/python sphinx
.venv-bench/bin/python -m sphinx -b html docs docs/_build/html   # 或 cd docs && make html PYTHON=../.venv-bench/bin/python
```

类型存根 `uniqc_cpp.pyi` 随 wheel 发布；基准结果文档见 [doc/benchmark.md](doc/benchmark.md)。

## 性能基准

[`benchmark/`](benchmark/README.md) 提供跨模拟器 CPU 基准套件：以 `uniqc_cpp` 为对象，
与主流 pip 可装 CPU 模拟器广泛对比（Qiskit Aer、Cirq、Google qsim、Qulacs、PennyLane
lightning、Qibo、quimb、QuTiP、Braket 本地模拟器；未安装的自动跳过），覆盖：

- **基线**：单线程 vs 多线程（现阶段仅 CPU）
- **线路族 × qubit 数**：`ghz` / `qft` / 分层随机 / `qaoa`，4 → 24 量子比特
- **噪声**：去极化、幅度阻尼、比特翻转（密度矩阵）与轨迹采样
- **多线程机制**：外部模拟器走内核线程旋钮（OMP/选项）；`uniqc_cpp` 内核自带
  全局多线程开关（`set_num_threads` / `set_parallel_enabled`），threads 档位直接
  测内核门级并行；`uniqc_sv_batch` 另保留 shot 级进程并行采样吞吐基线

```bash
uv venv .venv-bench --python 3.12 && uv pip install --python .venv-bench/bin/python \
    uniqc-cppsimulator matplotlib qiskit qiskit-aer cirq qsimcirq qulacs \
    pennylane pennylane-lightning qibo qibojit quimb qutip qutip-qip amazon-braket-sdk
.venv-bench/bin/python -m benchmark selftest                      # 适配器正确性检查
.venv-bench/bin/python -m benchmark run --preset smoke            # ~2 分钟冒烟
.venv-bench/bin/python -m benchmark run --preset standard --out benchmark/results.json
.venv-bench/bin/python -m benchmark plot && .venv-bench/bin/python -m benchmark report
```

默认对比对象是 PyPI 上最新的 `uniqc-cppsimulator` release；本轮为验证内核多线程，
从本地源码安装 dev 构建（`1.0.2.dev4`）。

### 最近一轮结果（2026-09-22，Xeon Gold 5118 × 48 核，本地 dev 构建 `1.0.2.dev4`）

理想态矢量、单线程、各线路最大可比规模（完整数据见 [`doc/benchmark.md`](doc/benchmark.md)）：

| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |
|---|---|---|---|---|
| ghz | 24 | Qiskit Aer (4.9 ms) | 1.82 s | ×372 |
| qaoa | 24 | Google qsim (3.21 s) | 69.7 s | ×22 |
| qft | 20 | Google qsim (224 ms) | 13.3 s | ×59 |
| random | 24 | Google qsim (3.15 s) | 27.3 s | ×9 |

**内核多线程首次生效**（threads=8 档位，全局 `set_num_threads` 门级并行）：

- 大规模加速 **×2.7–2.9**：ghz 24q 1.82 s → 0.67 s；random 24q 27.3 s → 10.2 s；
  qaoa 24q 69.7 s → 24.2 s；20q 约 ×1.7–1.8。≤16q 受线程启动开销与访存带宽限制收益甚微。
- threads=8 下 24q ghz：uniqc_sv（672 ms）已与 PennyLane lightning（655 ms）并肩，
  仅次于 Aer 的线路专用优化（2.1 ms）。
- 密度矩阵行循环同样并行：uniqc_dm 10q 去极化 **×1.7**（19.0 s → 11.0 s）。
- 采样吞吐（1024 shots）：进程级并行仍是王道 —— uniqc_sv_batch 16q **×7.7**
  （37.0 s → 4.8 s），8q 达 17.4k shots/s 超过 Aer 多线程（6.3k）；内核线程对
  轨迹采样仅 ×1.1（每条轨迹规模小、且无跨轨迹并行），两种机制各司其职。
- 小规模（≤8q）单线程：uniqc_sv 与 Qulacs 各拿下 8 个线路-规模组合中的 4 个。
- 噪声密度矩阵（去极化）：4q 处 uniqc_dm 最快（1.7 ms，比 Qulacs-DM 快 ~2.5×），
  10q 处落后 Aer（19.0 s vs 1.7 s）。

> 数字来自共享开发机（本轮有其他用户进程占用约 21 核，多线程加速比被低估）、
> 未做绑核等公平性控制，仅用于相对趋势；图表见
> [doc/benchmark.md](doc/benchmark.md)，原始 JSON 见 `doc/benchmark/results-2026-09-22.json`。

## 版本与兼容

- 本包版本与 UnifiedQuantum 独立演进。UnifiedQuantum 在其 `pyproject.toml` 中以 `uniqc-cppsimulator>=x.y,<z` 声明兼容区间。
- 破坏性 API 变更会提升 major 版本并在 CHANGELOG 中标注。

## 许可证

Apache License 2.0，见 [LICENSE](LICENSE)。
