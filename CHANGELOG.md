# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **合并 `doc/` 与 `docs/` 为唯一文档目录**：基准结果证据（报告、图表、JSON 快照）自 `doc/benchmark.md` + `doc/benchmark/` 移至 `docs/benchmark/report.md` + `docs/benchmark/`，与 Sphinx 源同处 `docs/`。`benchmark plot` / `benchmark report` 的默认输出目录、`docs/prepare.py` 的拷贝/链接重写、README/benchmark README/CI 触发路径与 `.gitignore` 同步更新；`README_summary.md` 的"相关文档"一节并入生成器（单一来源）。历史数据与图表内容不变（仅路径/相对链接调整）。

### Fixed

- **benchmark `selftest` 与 `run`/`list` 对未安装模拟器行为一致**：`python -m benchmark selftest` 现在先做与 `run` 相同的可用性探测——未安装的后端打印 `missing (原因)` 并跳过，不再把适配器构造时的 ImportError 记成"已知答案检查失败"；只有可到达且检查失败的后端（或 `--backends` 显式给出的未知名字）才使命令以非零退出。worker 侧 `run_selftest` 的构造异常也改为输出单后端失败记录而非让子进程无输出退出。配套地，`benchmark.backends` 注册表与 CLI 导入不再要求 numpy/matplotlib（`backends/util.py`、`qutip_sim.py` 的 numpy 与 `plotting.py` 的 matplotlib 改为调用点惰性导入），`list`/`selftest`/`run`/probe 在只装 `uniqc_cpp` 的机器可用，`plot` 缺绘图栈时给出明确错误。新增 CLI 语义与无 numpy 导入回归（`tests/test_benchmark.py`）。
- **基准图表标题/注释与 1.1.0 线程模型一致**：`thread_speedup` 副标题此前仍称 "uniqc_sv parallelism is shot-level"（1.1.0 起 uniqc_sv/uniqc_dm 为内核门级线程；shot 级进程并行属于 uniqc_sv_batch 且仅采样模式），`ideal_runtime` 图的单线程档位注释同步修正；`docs/benchmark/` 四张图由同一 `results-2026-09-22.json` 重新渲染（数据不变，仅标题文字）。
- `benchmark/README.md` 修正 standard 预设 qubit 扫描上限为 4→24（此前误写 26）；shots 行注明 standard=1024。

### Added

- **ruff lint 门禁**：`pyproject.toml` 固定规则集（E4/E7/E9/F/B/BLE/E402/EXE/RUF100，target py310），CI（Build-and-test）新增 lint job（固定 ruff 0.17.4）；`scripts/check_release.py` / `check_wheel_abi.py` 补可执行位。

## [1.1.0] - 2026-11-09

### Added

- **内核全局多线程**：新增进程级全局开关与线程数 API（`uniqc_cpp.set_parallel_enabled` / `is_parallel_enabled` / `set_num_threads` / `get_num_threads`，默认关闭、单线程，与历史行为完全一致）。态矢量全部门内核（含受控门）与密度算符行循环按 `std::thread` 连续分块并行（无新依赖，CMake 仅链接 `Threads::Threads`）；门操作结果与单线程数值一致（不同编译器的浮点收缩可能有末位差异），概率类读出（`pmeasure`/`get_prob`）还可能有浮点求和顺序差异；`rand()` 决策保留在调用线程；态矢量小于 2^14 幅度时自动回落单线程，密度矩阵按行循环总工作量决定。类型存根与 `docs/usage.rst` 同步更新。
- **benchmark 多线程基线接入内核线程**：`uniqc_sv` 后端改为 `option` 模式（threads 档位经全局 API 直接测内核门级并行，此前精确模式的 threads>1 档位被跳过）；新增 `uniqc_sv_batch` 后端保留原进程池 shot 级采样吞吐基线；`uniqc_dm` 同样改为 `option`。sampling 预设组加入 `uniqc_sv_batch`，相关文档（README / benchmark/README / docs）同步。

### Fixed

- **QRAM 原生入口的越界访问与高位静默丢失**：`StatevectorSimulator` 与 `DensityOperatorSimulator` 现在要求数据数组长度恰好为 `2^addr_size`，并拒绝超出 `data_size` 位宽的值，统一抛出 `ValueError`。此前过短数组会使两个后端段错误，超位宽值的高位会被静默忽略；有效调用语义与 UniQC `QRAM` 既有契约不变。新增 Python 参数化回归及 C++ 原生异常回归。
- **`StatevectorSimulator::measure_single_shot` 标量重载死循环**：`measure_single_shot({ qubit })` 的花括号初始化列表在重载决议中选中了标量重载自身，完美尾递归被编译器优化为无限循环——表现为挂起而非崩溃，1.0.1 及此前所有发布版本均受影响（list 重载不受影响，故既有测试未暴露）。现改为显式 `std::vector{ qubit }` 转发（与 `pmeasure` 标量重载同一写法）。新增带子进程超时保护的回归测试（`tests/test_bindings.py`）：旧版本上该测试失败而非挂死套件。
- **`benchmark.worker` 在 Windows 上不可导入**：顶层 `import resource`（Unix-only 标准库）改为带回退的守卫导入，无 `resource` 平台上峰值 RSS 记为 `null`；`python -m benchmark list` 等 CLI 与文档 autodoc 在 Windows 恢复可用。

### Added

- **Sphinx 文档（`docs/`）**：使用/构建/测试指南、基准套件使用、`benchmark` 包 API 参考（autodoc）与 `uniqc_cpp` 扩展 API 参考；补全 `benchmark` 包全部 docstring。构建：`python -m sphinx -b html docs docs/_build/html`（零告警）。
- **文档发布到 GitHub Pages**：`.github/workflows/docs-pages.yml` 在 `main` 分支文档相关变更后自动构建部署（`-W` 零告警门禁）。README / CHANGELOG / `doc/benchmark.md` / `benchmark/README.md` 与基准图表由 `docs/prepare.py` 在构建开始时自动拷入站点并重写站内链接（myst-parser），主题换为 furo；站点地址 <https://iai-ustc-quantum.github.io/uniqc-cppsimulator/>。
- **跨模拟器 CPU benchmark 套件（`benchmark/`）**：以 `uniqc_cpp` 为对象与主流 pip 可装 CPU 模拟器（Qiskit Aer、Cirq、qsim、Qulacs、PennyLane lightning、Qibo、quimb、QuTiP、Braket 本地模拟器等）对比；统一线路 IR + 注册表扩展点（线路族 / 噪声预设 / 后端适配器 / 矩阵预设 / 图表）；单线程 vs 多线程基线（外部模拟器走原生线程旋钮，`uniqc_cpp` 走进程池并行采样吞吐）；结果 JSON 落盘 + 图表 + 报告生成（`python -m benchmark run|plot|report`）。摘要见 [README"性能基准"](README.md#性能基准)，详情见 [docs/benchmark/report.md](docs/benchmark/report.md)，套件用法见 [benchmark/README.md](benchmark/README.md)。

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
