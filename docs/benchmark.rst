基准测试套件
============

``benchmark/`` 是跨模拟器 CPU 性能基准套件：以 ``uniqc_cpp`` 为对象，与主流
pip 可装 CPU 模拟器广泛对比，覆盖**单线程 vs 多线程**基线、**多线路族 × 多
qubit 数**与**多噪声模型**。完整方法论与扩展指南见
`benchmark/README.md <../benchmark/README.md>`_；结果摘要见仓库 README"性能基准"，
详细数据与图表见 `doc/benchmark.md <../doc/benchmark.md>`_。

对比对象（未安装的自动跳过并记录原因）：Qiskit Aer（statevector /
density_matrix）、Cirq（Simulator / DensityMatrixSimulator）、Google qsim
（qsimcirq）、Qulacs（QuantumState / DensityMatrix）、PennyLane
lightning.qubit、Qibo（qibojit）、quimb、QuTiP qip、Amazon Braket 本地模拟器，
以及 Qrack（pyqrack，需要系统 Qrack 库）。

快速开始
--------

.. code-block:: bash

   uv venv .venv-bench --python 3.12
   uv pip install --python .venv-bench/bin/python uniqc-cppsimulator \
       matplotlib qiskit qiskit-aer cirq qsimcirq qulacs pennylane pennylane-lightning \
       qibo qibojit quimb qutip qutip-qip amazon-braket-sdk

   .venv-bench/bin/python -m benchmark list          # 已注册后端/线路/噪声/预设
   .venv-bench/bin/python -m benchmark selftest      # 适配器正确性检查
   .venv-bench/bin/python -m benchmark run --preset smoke        # ~2 分钟冒烟
   .venv-bench/bin/python -m benchmark run --preset standard --out benchmark/results.json
   .venv-bench/bin/python -m benchmark plot    --results benchmark/results.json
   .venv-bench/bin/python -m benchmark report  --results benchmark/results.json

CLI 子命令： ``list`` / ``selftest`` / ``run`` / ``plot`` / ``report``。
其中 ``run`` 支持 ``--backends`` / ``--limit`` / ``--resume`` （断点续跑，已完成 case 复用）。

测什么
------

- **线路族**：``ghz`` / ``qft`` / 分层随机 ``random`` / ``qaoa``，按
  ``(n_qubits, depth, seed)`` 参数化，由 :func:`benchmark.registry.CIRCUITS` 注册；
- **qubit 数**：standard 预设扫描 4 → 24（每个后端有各自上限）；
- **噪声**：``none`` / ``depol`` / ``depol-strong`` / ``adamp`` / ``bitflip``，
  以内联通道算子插入门后（见 :func:`benchmark.ir.apply_noise`）；
- **shots**：0（精确概率读出）或 >0（轨迹采样吞吐）；
- **线程**：1 vs N。

指标：warm-up 1 次 + N 次重复的墙钟时间（median/mean/min/std）、峰值 RSS；
读出量统一为标量 ``P(q0=1)``，避免各后端输出格式差异污染计时。

单线程 vs 多线程基线
--------------------

各后端拿到 ``threads`` 参数的方式（``BenchmarkBackend.threads_mode``）：

- ``option`` —— 后端原生线程选项（Aer ``max_parallel_threads``、qsim
  ``cpu_threads``、qibo ``set_threads``、uniqc ``set_num_threads`` +
  ``set_parallel_enabled``，内核门级并行）；
- ``env`` —— 由 runner 在 worker 子进程 import 前通过 ``OMP_NUM_THREADS``
  等环境变量固定（qulacs、lightning、quimb、cirq、qutip、braket）；
- ``batch`` —— **uniqc_sv_batch 专属**：轨迹在单线程内核上由进程池并行跑
  独立 shots，测采样吞吐（等价 shot-parallelism）；
- ``none`` —— 单线程内核无旋钮。

.. note::
   ``batch`` 与 ``option``/``env`` 的并行机制不同（任务级 vs 门级并行），
   加速比数值不可直接互比——图表因此分开展示。

方法论
------

- 每个 case 在独立子进程执行（线程环境变量在 import 前固定、结果隔离）；
  runner 串行调度保证计时隔离；
- 每案例超时则记 ``timeout`` 并继续；
- 运行前对每个后端跑 4 条已知答案微线路（含比特序校验），未通过者被
  排除出结果；
- 基准未做绑核/独占机器等公平性控制，结果用于相对趋势。

扩展点
------

- **新线路族**：``benchmark/circuits.py`` 实现 builder 并 ``@register_circuit``；
- **新噪声**：``benchmark/noise.py`` 加 ``NoisePreset``；
- **新模拟器**：``benchmark/backends/`` 继承 ``BenchmarkBackend`` 实现 ``run()``，加 ``@register_backend``；
- **新矩阵**：``benchmark/presets.py`` 加 ``Group`` 或 ``PRESETS`` 条目；
- **新图表**：``benchmark/plotting.py`` 实现 ``fig_xxx(data, out_dir)`` 并 ``@plotter``。

API 细节见 :doc:`api_benchmark`。
