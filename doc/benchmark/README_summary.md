# 基准结果摘要

运行环境：Intel(R) Xeon(R) Gold 5118 CPU @ 2.30GHz（48 核），Python 3.12.13，threads=1；完整环境与版本表见[详情文档](doc/benchmark.md)。

| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |
|---|---|---|---|---|
| ghz | 24 | Qiskit Aer statevector (4.89 ms) | 1.82 s | ×371.7 |
| qaoa | 24 | Google qsim (qsimcirq) (3.21 s) | 69.72 s | ×21.7 |
| qft | 20 | Google qsim (qsimcirq) (224 ms) | 13.26 s | ×59.1 |
| random | 24 | Google qsim (qsimcirq) (3.15 s) | 27.28 s | ×8.7 |

## 相关文档

- [完整结果与图表](doc/benchmark.md) —— 全部数据表、图与注意事项
- [基准方法论与扩展指南](../../benchmark/README.md) —— 测量维度、线程模型、如何新增线路/后端
- [仓库 README · 性能基准](../../README.md#性能基准) —— 面向使用者的结果解读
- [快速上手](../../README.md#快速上手) —— 安装与第一个模拟器示例
