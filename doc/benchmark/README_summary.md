运行环境：Intel(R) Xeon(R) Gold 5118 CPU @ 2.30GHz（48 核），Python 3.12.13，threads=1；完整环境与版本表见[详情文档](doc/benchmark.md)。

| 线路 | 最大可比 qubits | 最快 | uniqc_sv | 倍差 |
|---|---|---|---|---|
| ghz | 24 | Qiskit Aer statevector (4.89 ms) | 1.82 s | ×371.7 |
| qaoa | 24 | Google qsim (qsimcirq) (3.21 s) | 69.72 s | ×21.7 |
| qft | 20 | Google qsim (qsimcirq) (224 ms) | 13.26 s | ×59.1 |
| random | 24 | Google qsim (qsimcirq) (3.15 s) | 27.28 s | ×8.7 |
