uniqc_cpp 扩展 API 参考
=======================

``uniqc_cpp`` 是 pybind11 构建的 C++ 扩展（分发名 ``uniqc-cppsimulator``），
提供两个模拟器类与一个全局 RNG。方法签名随类型存根
`uniqc_cpp.pyi <https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator/blob/main/uniqc_cpp.pyi>`_
一起发布，IDE / 类型检查器可直接使用。

两个类的门操作 API 相同；差异在于：

- ``StatevectorSimulator``：态矢量（最多 30 量子比特）。噪声通道为**随机轨迹**
  （Monte Carlo，每次调用采样一条轨迹）；支持 ``measure_single_shot``。
- ``DensityOperatorSimulator``：密度算符（最多 10 量子比特）。噪声通道为
  **确定性** 超算符演化。

约定
----

- 量子比特下标从 0 开始；角度一律为弧度。基态整数中 qubit 0 是最低有效位。
- 多数量值门带可选 ``global_controller``（全局控制位列表）与 ``dagger``
  （取逆）参数。
- ``pmeasure``/``get_prob`` 等概率读出和 ``measure_single_shot`` 单次采样不改变
  量子态；``measure_qubit`` 会坍缩态，``reset_qubit`` 在测量后按需施加 X 门。
- ``pmeasure([q0, q1, ...])`` 的返回索引和 ``measure_single_shot([q0, q1, ...])``
  的返回整数都把**列表第一个量子比特放在最低有效位**。后者返回 Python ``int``；
  相同线程内重设 ``seed`` 会复现之后的随机噪声与测量序列。
- QRAM 地址和数据列表也采用首元素为最低有效位的顺序；数据数组必须恰好有
  ``2^len(addr_qubits)`` 项，每项必须能用 ``len(data_qubits)`` 位表示，否则抛出
  ``ValueError``，不会越界访问或静默丢弃高位。
- 两个后端都是稠密表示：态矢量含 ``2^n`` 个 ``complex<double>``，密度矩阵含
  ``4^n`` 个。仅 30 比特态矢量本身即需 16 GiB，临时副本另计；10 比特密度矩阵
  本身为 16 MiB。上限不是容量保证，也不表示支持任意宽寄存器或稀疏大状态。
- 多线程设置是进程级全局配置，但各模拟器实例及随机数引擎不保证多线程并发调用
  安全；请在调用线程中设置种子并执行该线程的实验。

参见
----

- :doc:`usage` —— 安装方式与最小运行示例
- :doc:`benchmark` —— 这两个内核与竞品的性能对比
- :doc:`includes/changelog` —— 内核版本历史
- 类型存根 `uniqc_cpp.pyi <https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator/blob/main/uniqc_cpp.pyi>`_

模块级函数
----------

.. autofunction:: uniqc_cpp.seed

.. autofunction:: uniqc_cpp.rand

StatevectorSimulator
--------------------

.. autoclass:: uniqc_cpp.StatevectorSimulator
   :members:
   :undoc-members:
   :special-members: __init__

DensityOperatorSimulator
------------------------

.. autoclass:: uniqc_cpp.DensityOperatorSimulator
   :members:
   :undoc-members:
   :special-members: __init__
