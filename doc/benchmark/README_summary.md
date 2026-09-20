运行环境：Intel(R) Xeon(R) Gold 5118 CPU @ 2.30GHz（48 核），Python 3.12.13，threads=1；完整环境与版本表见[详情文档](doc/benchmark.md)。

| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |
|---|---|---|---|---|
| ghz | 24 | Qiskit Aer statevector (5.08 ms) | 1.66 s | ×327.5 |
| qaoa | 24 | Google qsim (qsimcirq) (2.09 s) | 64.31 s | ×30.7 |
| qft | 20 | Google qsim (qsimcirq) (214 ms) | 12.72 s | ×59.5 |
| random | 24 | Google qsim (qsimcirq) (1.98 s) | 24.79 s | ×12.5 |
