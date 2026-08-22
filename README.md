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

## 版本与兼容

- 本包版本与 UnifiedQuantum 独立演进。UnifiedQuantum 在其 `pyproject.toml` 中以 `uniqc-cppsimulator>=x.y,<z` 声明兼容区间。
- 破坏性 API 变更会提升 major 版本并在 CHANGELOG 中标注。

## 许可证

Apache License 2.0，见 [LICENSE](LICENSE)。
