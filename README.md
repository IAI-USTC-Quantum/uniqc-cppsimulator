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

## 性能基准

[`benchmark/`](benchmark/README.md) 提供跨模拟器 CPU 基准套件：以 `uniqc_cpp` 为对象，
与主流 pip 可装 CPU 模拟器广泛对比（Qiskit Aer、Cirq、Google qsim、Qulacs、PennyLane
lightning、Qibo、quimb、QuTiP、Braket 本地模拟器；未安装的自动跳过），覆盖：

- **基线**：单线程 vs 多线程（现阶段仅 CPU）
- **线路族 × qubit 数**：`ghz` / `qft` / 分层随机 / `qaoa`，4 → 24 量子比特
- **噪声**：去极化、幅度阻尼、比特翻转（密度矩阵）与轨迹采样
- **多线程机制**：外部模拟器走内核线程旋钮（OMP/选项）；`uniqc_cpp` 内核为单线程且
  绑定不释放 GIL，多线程基线为 **shot 级进程并行采样吞吐**

```bash
uv venv .venv-bench --python 3.12 && uv pip install --python .venv-bench/bin/python \
    uniqc-cppsimulator matplotlib qiskit qiskit-aer cirq qsimcirq qulacs \
    pennylane pennylane-lightning qibo qibojit quimb qutip qutip-qip amazon-braket-sdk
.venv-bench/bin/python -m benchmark selftest                      # 适配器正确性检查
.venv-bench/bin/python -m benchmark run --preset smoke            # ~2 分钟冒烟
.venv-bench/bin/python -m benchmark run --preset standard --out benchmark/results.json
.venv-bench/bin/python -m benchmark plot && .venv-bench/bin/python -m benchmark report
```

对比对象是 PyPI 上最新的 `uniqc-cppsimulator` release（未指定版本时自动取最新）。

### 最近一轮结果（2026-09-20，Xeon Gold 5118 × 48 核，PyPI release `1.0.1`）

理想态矢量、单线程、各线路最大可比规模（完整数据见 [`doc/benchmark.md`](doc/benchmark.md)）：

| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |
|---|---|---|---|---|
| ghz | 24 | Qiskit Aer (5.1 ms) | 1.66 s | ×328 |
| qaoa | 24 | Google qsim (2.09 s) | 64.3 s | ×31 |
| qft | 20 | Google qsim (214 ms) | 12.72 s | ×60 |
| random | 24 | Google qsim (1.98 s) | 24.8 s | ×13 |

- 小规模（≤8q）ideal 模拟 uniqc_sv 在 80 个数据点中 60 个最快（其余为 Qulacs）；
  大规模落后于多线程 C++ 内核（当前内核为单线程实现）。
- 多线程基线：Aer/qsim/Qulacs 内核级并行在 24q 处约 2–8×；uniqc_sv shot 级进程并行
  采样在 16q 处 **×6.9**（53.3 s → 7.7 s / 1024 shots）。
- 噪声密度矩阵（去极化）：4q 处 uniqc_dm 最快（0.9 ms，比 Qulacs-DM 快 ~7×），
  10q 处落后 Aer（13.9 s vs 1.7 s）。
- 轨迹采样吞吐（1024 shots）：uniqc_sv 在 8q/16q 均高于 Aer（6.2k/19 shots/s vs 2.6k/12）。

> 数字来自共享开发机、未做绑核等公平性控制，仅用于相对趋势；图表见
> [doc/benchmark.md](doc/benchmark.md)，原始 JSON 见 `doc/benchmark/results-2026-09-20.json`。

## 版本与兼容

- 本包版本与 UnifiedQuantum 独立演进。UnifiedQuantum 在其 `pyproject.toml` 中以 `uniqc-cppsimulator>=x.y,<z` 声明兼容区间。
- 破坏性 API 变更会提升 major 版本并在 CHANGELOG 中标注。

## 许可证

Apache License 2.0，见 [LICENSE](LICENSE)。
