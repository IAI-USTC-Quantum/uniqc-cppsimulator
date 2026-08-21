# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-21

初始独立版本。C++ 模拟器自 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) v0.0.17 拆分为独立仓库，import 名保持 `uniqc_cpp` 不变，API 与拆分前完全兼容。

- `StatevectorSimulator`（态矢量，最多 30 量子比特）与 `DensityOperatorSimulator`（密度算符，最多 10 量子比特，含噪声通道）
- QRAM 指令支持与参数校验
- Release 构建安全加固（stack protector / FORTIFY / relro）
- Python 绑定测试套件（`tests/`）与 C++ 原生冒烟测试
- 类型存根 `uniqc_cpp.pyi` 随 wheel 一起发布
