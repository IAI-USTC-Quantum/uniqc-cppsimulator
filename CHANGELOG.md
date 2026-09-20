# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`StatevectorSimulator::measure_single_shot` 标量重载死循环**：`measure_single_shot({ qubit })` 的花括号初始化列表在重载决议中选中了标量重载自身，完美尾递归被编译器优化为无限循环——表现为挂起而非崩溃，1.0.1 及此前所有发布版本均受影响（list 重载不受影响，故既有测试未暴露）。现改为显式 `std::vector{ qubit }` 转发（与 `pmeasure` 标量重载同一写法）。新增带子进程超时保护的回归测试（`tests/test_bindings.py`）：旧版本上该测试失败而非挂死套件。

### Added

- **跨模拟器 CPU benchmark 套件（`benchmark/`）**：以 `uniqc_cpp` 为对象与主流 pip 可装 CPU 模拟器（Qiskit Aer、Cirq、qsim、Qulacs、PennyLane lightning、Qibo、quimb、QuTiP、Braket 本地模拟器等）对比；统一线路 IR + 注册表扩展点（线路族 / 噪声预设 / 后端适配器 / 矩阵预设 / 图表）；单线程 vs 多线程基线（外部模拟器走原生线程旋钮，`uniqc_cpp` 走进程池并行采样吞吐）；结果 JSON 落盘 + 图表 + 报告生成（`python -m benchmark run|plot|report`）。摘要见 README"性能基准"，详情见 `doc/benchmark.md`。

## [1.0.1] - 2026-08-23

### Fixed

- **`StatevectorSimulator::twoqubit_depolarizing` 去极化概率被进程内首次调用固化**：1.0.0 中 Kraus 概率向量被误声明为 `const static` 局部变量，只在首次调用时初始化，之后同进程内所有调用静默沿用第一次的 `p`（实测错误率被"钉死"，且密度算符实现无此问题，两后端行为不一致）。现改为每次调用按当前 `p` 构建。新增同进程交变 `p` 的回归测试（`tests/test_bindings.py`）。

### Removed

- 清理 `qopcode.cpp` 中整段注释掉的废弃代码（`string_to_UnitaryType` / `string_to_NoiseType` / `gate_qubit_count`）。

## [1.0.0] - 2026-08-21

初始独立版本。C++ 模拟器自 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) v0.0.17 拆分为独立仓库，import 名保持 `uniqc_cpp` 不变，API 与拆分前完全兼容。

- `StatevectorSimulator`（态矢量，最多 30 量子比特）与 `DensityOperatorSimulator`（密度算符，最多 10 量子比特，含噪声通道）
- QRAM 指令支持与参数校验
- Release 构建安全加固（stack protector / FORTIFY / relro）
- Python 绑定测试套件（`tests/`）与 C++ 原生冒烟测试
- 类型存根 `uniqc_cpp.pyi` 随 wheel 一起发布
