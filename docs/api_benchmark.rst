benchmark 包 API 参考
=====================

``benchmark`` 是纯 Python 包（唯一要求的环境依赖是各模拟器 wheel 与
matplotlib），入口为 ``python -m benchmark``。模块按数据流组织：IR → 注册表 →
线路/噪声生成 → 后端适配 → 运行器 → 图表/报告。

线路中间表示
------------

.. automodule:: benchmark.ir

注册表
------

.. automodule:: benchmark.registry

线路族
------

.. automodule:: benchmark.circuits

噪声预设
--------

.. automodule:: benchmark.noise

矩阵预设
--------

.. automodule:: benchmark.presets

后端适配器
----------

基类契约（线程机制、能力声明、支持性检查）：

.. automodule:: benchmark.backends.base

数值辅助：

.. automodule:: benchmark.backends.util

具体适配器（每个文件顶部 docstring 说明该后端的线程模式与特殊处理）：

.. automodule:: benchmark.backends.uniqc_sv
.. automodule:: benchmark.backends.uniqc_dm
.. automodule:: benchmark.backends.aer
.. automodule:: benchmark.backends.cirq_sim
.. automodule:: benchmark.backends.qsimcirq_sim
.. automodule:: benchmark.backends.qulacs_sim
.. automodule:: benchmark.backends.lightning_sim
.. automodule:: benchmark.backends.qibo_sim
.. automodule:: benchmark.backends.quimb_sim
.. automodule:: benchmark.backends.qutip_sim
.. automodule:: benchmark.backends.braket_sim
.. automodule:: benchmark.backends.pyqrack_sim

运行器与 worker
---------------

.. automodule:: benchmark.runner

.. automodule:: benchmark.worker

图表与报告
----------

.. automodule:: benchmark.plotting

.. automodule:: benchmark.report

命令行入口
----------

.. automodule:: benchmark.cli
