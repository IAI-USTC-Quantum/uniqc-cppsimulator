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

- 量子比特下标从 0 开始；角度一律为弧度。
- 多数量值门带可选 ``global_controller``（全局控制位列表）与 ``dagger``
  （取逆）参数。
- ``pmeasure``/``get_prob`` 等读出方法不改变量子态；``measure_qubit`` /
  ``measure_single_shot`` 会坍缩态。

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
