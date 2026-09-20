# Benchmark 详情

本页由 `python -m benchmark report` 生成；方法论、矩阵定义与扩展方法见
[benchmark/README.md](../benchmark/README.md)，摘要见[仓库 README](../README.md#性能基准)。

## 运行环境

| field | value |
|---|---|
| 时间 | 2026-09-20T14:38:34+08:00 |
| 主机 | inspur-NF5466M5 |
| CPU | Intel(R) Xeon(R) Gold 5118 CPU @ 2.30GHz × 48 cores |
| 内存 | 126 GB |
| Python | 3.12.13 |
| 平台 | Linux-7.0.0-30-generic-x86_64-with-glibc2.39 |

**模拟器版本**

| backend | version | selftest |
|---|---|---|
| Qiskit Aer density_matrix | 0.17.2 | ✅ |
| Qiskit Aer statevector | 0.17.2 | ✅ |
| Braket LocalSimulator (NumPy) | 1.0.1 | ✅ |
| Cirq DensityMatrixSimulator | 1.7.0 | ✅ |
| Cirq Simulator (NumPy) | 1.7.0 | ✅ |
| PennyLane lightning.qubit | 0.45.1 | ✅ |
| Qrack (pyqrack) | 未安装 (OSError: /usr/lib/qrack/libqrack_pinvoke.so: cannot open shared object file: No such file or directory) | — |
| Qibo (qibojit) | 0.3.5 | ✅ |
| Google qsim (qsimcirq) | 0.22.1 | ✅ |
| quimb dense Circuit | 1.15.0 | ✅ |
| Qulacs DensityMatrix | 0.6.14 | ✅ |
| Qulacs QuantumState | 0.6.14 | ✅ |
| QuTiP qip CircuitSimulator | 0.4.2 | ✅ |
| uniqc_cpp DensityOperatorSimulator | 1.0.1 | ✅ |
| uniqc_cpp StatevectorSimulator | 1.0.1 | ✅ |

**未参与对比的后端**：`pyqrack` (OSError: /usr/lib/qrack/libqrack_pinvoke.so: cannot open shared object file: No such file or directory)

## 理想态矢量模拟（无噪声，读出精确概率）

### ideal statevector — median wall time


#### threads = 1

| backend | ghz(d4) n=4 | ghz(d4) n=8 | ghz(d4) n=12 | ghz(d4) n=16 | ghz(d4) n=20 | ghz(d4) n=24 | qaoa(d4) n=4 | qaoa(d4) n=8 | qaoa(d4) n=12 | qaoa(d4) n=16 | qaoa(d4) n=20 | qaoa(d4) n=24 | qft(d4) n=4 | qft(d4) n=8 | qft(d4) n=12 | qft(d4) n=16 | qft(d4) n=20 | qft(d4) n=24 | random(d4) n=4 | random(d4) n=8 | random(d4) n=12 | random(d4) n=16 | random(d4) n=20 | random(d4) n=24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniqc_cpp StatevectorSimulator | **0.04 ms** | 0.14 ms | 1.46 ms | 22 ms | 383 ms | 1.66 s | **0.16 ms** | **0.71 ms** | 8.96 ms | 180 ms | 3.62 s | 64.31 s | **0.09 ms** | 0.85 ms | 18 ms | 504 ms | 12.72 s | — | **0.09 ms** | **0.37 ms** | 3.88 ms | 73 ms | 1.62 s | 24.79 s |
| Qiskit Aer statevector | 2.15 ms | 2.99 ms | 3.39 ms | 3.99 ms | **4.31 ms** | **5.08 ms** | 8.07 ms | 13 ms | 22 ms | 67 ms | 791 ms | 14.50 s | 5.78 ms | 11 ms | 32 ms | 89 ms | 928 ms | 19.13 s | 5.67 ms | 8.47 ms | 9.50 ms | 60 ms | 951 ms | 18.01 s |
| Braket LocalSimulator (NumPy) | 11 ms | 15 ms | 26 ms | 41 ms | — | — | 64 ms | 123 ms | 262 ms | 359 ms | — | — | 32 ms | 111 ms | 376 ms | 757 ms | — | — | 34 ms | 63 ms | 128 ms | 180 ms | — | — |
| Cirq Simulator (NumPy) | 2.60 ms | 3.87 ms | 5.59 ms | 14 ms | 115 ms | — | 15 ms | 25 ms | 48 ms | 182 ms | 2.25 s | — | 5.91 ms | 19 ms | 43 ms | 133 ms | 1.30 s | — | 6.76 ms | 14 ms | 25 ms | 84 ms | 1.17 s | — |
| PennyLane lightning.qubit | 0.62 ms | 1.02 ms | 1.18 ms | **2.23 ms** | 19 ms | 648 ms | 3.54 ms | 8.33 ms | 12 ms | 27 ms | 345 ms | 9.39 s | 1.72 ms | 7.05 ms | 15 ms | 48 ms | 830 ms | 24.92 s | 2.10 ms | 3.87 ms | 5.89 ms | **13 ms** | 167 ms | 4.59 s |
| Qibo (qibojit) | 65 ms | 101 ms | 89 ms | 111 ms | 156 ms | 969 ms | 571 ms | 1.12 s | 1.51 s | 2.00 s | 2.49 s | 11.71 s | 315 ms | 851 ms | 2.00 s | 3.58 s | 6.92 s | 29.69 s | 216 ms | 514 ms | 733 ms | 1.13 s | 1.26 s | 5.28 s |
| Google qsim (qsimcirq) | 0.69 ms | 1.18 ms | 1.87 ms | 3.32 ms | 36 ms | 761 ms | 5.09 ms | 9.69 ms | 14 ms | **26 ms** | **102 ms** | **2.09 s** | 2.53 ms | 8.31 ms | 18 ms | **38 ms** | **214 ms** | **5.28 s** | 2.63 ms | 4.75 ms | 7.06 ms | 13 ms | **87 ms** | **1.98 s** |
| quimb dense Circuit | 5.51 ms | 14 ms | 34 ms | 105 ms | — | — | 58 ms | 134 ms | 212 ms | 254 ms | — | — | 463 ms | 107 ms | 249 ms | 475 ms | — | — | 30 ms | 58 ms | 105 ms | 153 ms | — | — |
| Qulacs QuantumState | 0.06 ms | **0.10 ms** | **0.29 ms** | 4.37 ms | 75 ms | 1.36 s | 0.36 ms | 0.76 ms | **2.81 ms** | 36 ms | 745 ms | 15.99 s | 0.18 ms | **0.67 ms** | **2.99 ms** | 50 ms | 1.37 s | 36.16 s | 0.20 ms | 0.38 ms | **1.55 ms** | 21 ms | 417 ms | 8.55 s |
| QuTiP qip CircuitSimulator | 1.08 ms | 2.16 ms | 5.38 ms | — | — | — | 7.80 ms | 18 ms | 56 ms | — | — | — | 4.27 ms | 17 ms | 88 ms | — | — | — | 4.03 ms | 8.83 ms | 28 ms | — | — | — |

#### threads = 8

| backend | ghz(d4) n=4 | ghz(d4) n=8 | ghz(d4) n=12 | ghz(d4) n=16 | ghz(d4) n=20 | ghz(d4) n=24 | qaoa(d4) n=4 | qaoa(d4) n=8 | qaoa(d4) n=12 | qaoa(d4) n=16 | qaoa(d4) n=20 | qaoa(d4) n=24 | qft(d4) n=4 | qft(d4) n=8 | qft(d4) n=12 | qft(d4) n=16 | qft(d4) n=20 | qft(d4) n=24 | random(d4) n=4 | random(d4) n=8 | random(d4) n=12 | random(d4) n=16 | random(d4) n=20 | random(d4) n=24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniqc_cpp StatevectorSimulator | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Qiskit Aer statevector | 2.19 ms | 2.74 ms | 3.25 ms | 4.01 ms | **4.41 ms** | **3.71 ms** | 7.19 ms | 12 ms | 22 ms | 37 ms | 149 ms | 2.06 s | 5.20 ms | 12 ms | 36 ms | 63 ms | 205 ms | 2.76 s | 4.84 ms | 8.66 ms | 16 ms | 23 ms | 178 ms | 2.90 s |
| Braket LocalSimulator (NumPy) | 12 ms | 14 ms | 25 ms | 32 ms | — | — | 72 ms | 120 ms | 273 ms | 352 ms | — | — | 32 ms | 112 ms | 400 ms | 836 ms | — | — | 34 ms | 64 ms | 130 ms | 178 ms | — | — |
| Cirq Simulator (NumPy) | 2.67 ms | 3.86 ms | 5.65 ms | 14 ms | 123 ms | — | 12 ms | 28 ms | 48 ms | 182 ms | 2.29 s | — | 5.95 ms | 20 ms | 44 ms | 133 ms | 1.29 s | — | 7.67 ms | 13 ms | 24 ms | 86 ms | 1.25 s | — |
| PennyLane lightning.qubit | 0.59 ms | 0.92 ms | 1.31 ms | 2.24 ms | 20 ms | 658 ms | 3.68 ms | 7.89 ms | 12 ms | 27 ms | 361 ms | 9.57 s | 1.69 ms | 6.95 ms | 16 ms | 50 ms | 815 ms | 25.06 s | 2.07 ms | 3.93 ms | 6.01 ms | 13 ms | 163 ms | 4.46 s |
| Qibo (qibojit) | 0.24 ms | 0.41 ms | 0.61 ms | **1.26 ms** | 11 ms | 408 ms | 2.86 ms | 6.75 ms | 9.12 ms | 19 ms | 147 ms | 7.48 s | 1.35 ms | 5.12 ms | 11 ms | 30 ms | 398 ms | 16.46 s | 1.67 ms | 3.15 ms | 4.81 ms | 10 ms | 71 ms | 3.60 s |
| Google qsim (qsimcirq) | 0.70 ms | 1.25 ms | 1.74 ms | 2.90 ms | 19 ms | 462 ms | 5.21 ms | 10 ms | 15 ms | 21 ms | **52 ms** | **1.11 s** | 2.47 ms | 8.42 ms | 18 ms | 34 ms | **95 ms** | **2.07 s** | 2.79 ms | 5.09 ms | 7.02 ms | 11 ms | **40 ms** | **1.06 s** |
| quimb dense Circuit | 5.50 ms | 14 ms | 34 ms | 107 ms | — | — | 63 ms | 124 ms | 179 ms | 284 ms | — | — | 470 ms | 114 ms | 244 ms | 476 ms | — | — | 35 ms | 61 ms | 212 ms | 135 ms | — | — |
| Qulacs QuantumState | **0.06 ms** | **0.09 ms** | **0.29 ms** | 3.21 ms | 63 ms | 1.09 s | **0.39 ms** | **0.75 ms** | **3.48 ms** | **14 ms** | 174 ms | 6.05 s | **0.18 ms** | **0.67 ms** | **3.54 ms** | **16 ms** | 246 ms | 14.08 s | **0.20 ms** | **0.38 ms** | **1.85 ms** | **7.82 ms** | 117 ms | 2.71 s |
| QuTiP qip CircuitSimulator | 1.08 ms | 2.15 ms | 5.41 ms | — | — | — | 7.81 ms | 17 ms | 56 ms | — | — | — | 4.25 ms | 16 ms | 89 ms | — | — | — | 4.79 ms | 8.93 ms | 28 ms | — | — | — |


## 噪声密度矩阵模拟

### density matrix — median wall time


#### threads = 1

| backend | random(d2) n=4 | random(d2) n=6 | random(d2) n=8 | random(d2) n=10 |
|---|---|---|---|---|
| uniqc_cpp DensityOperatorSimulator | **0.95 ms** | **26 ms** | 647 ms | 13.90 s |
| Qiskit Aer density_matrix | 58 ms | 85 ms | **169 ms** | **1.68 s** |
| Cirq DensityMatrixSimulator | 53 ms | 234 ms | 2.93 s | 47.62 s |
| Qulacs DensityMatrix | 6.70 ms | 44 ms | 1.20 s | 25.48 s |

#### threads = 8

| backend | random(d2) n=4 | random(d2) n=6 | random(d2) n=8 | random(d2) n=10 |
|---|---|---|---|---|
| uniqc_cpp DensityOperatorSimulator | **1.24 ms** | **20 ms** | 552 ms | 14.17 s |
| Qiskit Aer density_matrix | 57 ms | 86 ms | **100 ms** | **1.09 s** |
| Cirq DensityMatrixSimulator | 57 ms | 232 ms | 2.97 s | 58.06 s |
| Qulacs DensityMatrix | 53 ms | 47 ms | 1.19 s | 12.49 s |


## 轨迹采样（shots 模式）

| backend | qubits | shots | threads | median time | shots/s |
|---|---|---|---|---|---|
| Qiskit Aer statevector | 8 | 1024 | 1 | 396 ms | 2,585 |
| Qiskit Aer statevector | 8 | 1024 | 8 | 292 ms | 3,501 |
| Qiskit Aer statevector | 16 | 1024 | 1 | 82.40 s | 12 |
| Qiskit Aer statevector | 16 | 1024 | 8 | 8.72 s | 117 |
| uniqc_cpp StatevectorSimulator | 8 | 1024 | 1 | 164 ms | 6,230 |
| uniqc_cpp StatevectorSimulator | 8 | 1024 | 8 | 92 ms | 11,111 |
| uniqc_cpp StatevectorSimulator | 16 | 1024 | 1 | 53.26 s | 19 |
| uniqc_cpp StatevectorSimulator | 16 | 1024 | 8 | 7.69 s | 133 |
| uniqc_cpp StatevectorSimulator | 20 | 1024 | 8 | 134.35 s | 8 |

## 图表

![ideal runtime](benchmark/ideal_runtime_vs_qubits.png)

![thread speedup](benchmark/thread_speedup.png)

![noise runtime](benchmark/noise_runtime_vs_qubits.png)

![sampling throughput](benchmark/sampling_throughput.png)

## 结果 JSON

原始数据（含每次重复的耗时、RSS、p_q0_1）：`benchmark/results.json`（运行时由 `--out` 指定，仓库内快照见 `doc/benchmark/results-<date>.json`）。

## 注意事项

- 本轮 uniqc_cpp 使用 PyPI 最新 release `1.0.1`。
- **已知 release bug（源码已修复，待发版）**：`StatevectorSimulator.measure_single_shot(int)` 标量重载会无限递归死循环（`{ qubit }` 花括号初始化在重载决议中选中标量重载自身，尾递归被优化为循环；本轮测量的 1.0.1 release 仍受影响）。list 重载正常，采样适配器统一使用 `measure_single_shot([0])` 规避。
- 线程维度机制不同：外部模拟器为内核内门级并行（OMP/选项），uniqc_sv 为**进程池 shot 级并行**（采样吞吐），二者数值不可直接互比。
- 基准未做绑核/独占机器等公平性控制（共享开发机），结果反映相对趋势。
- 未参与对比：`pyqrack` — OSError: /usr/lib/qrack/libqrack_pinvoke.so: cannot open shared object file: No such file or directory
