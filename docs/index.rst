uniqc-cppsimulator 文档
========================

UnifiedQuantum 的 C++ 量子线路模拟内核，独立发版，通过 pybind11 暴露为
**``uniqc_cpp``** Python 扩展模块：

- ``StatevectorSimulator`` —— 态矢量模拟器（最多 30 量子比特）
- ``DensityOperatorSimulator`` —— 密度算符模拟器（最多 10 量子比特，支持噪声通道）

.. toctree::
   :maxdepth: 2
   :caption: 开始

   usage
   includes/readme

.. toctree::
   :maxdepth: 2
   :caption: 基准测试

   benchmark
   includes/benchmark-methodology
   includes/benchmark-summary
   includes/benchmark-results

.. toctree::
   :maxdepth: 2
   :caption: API 参考

   api_uniqc_cpp
   api_benchmark

.. toctree::
   :caption: 项目

   includes/changelog

常用入口
--------

- :doc:`usage` —— 安装、源码构建与测试
- :doc:`benchmark` —— 跨模拟器 CPU 基准套件的使用方法
- :doc:`includes/benchmark-summary` —— 一页纸结果摘要
- :doc:`includes/benchmark-results` —— 最近一轮基准结果的数据与图表
- :doc:`api_uniqc_cpp` —— ``uniqc_cpp`` 扩展 API 参考
- :doc:`api_benchmark` —— ``benchmark`` 包 API 参考

其它资料
--------

- `GitHub 仓库 <https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator>`_ —— 源码与 issue
- `UnifiedQuantum <https://github.com/IAI-USTC-Quantum/UnifiedQuantum>`_ —— 上层项目
- `UnifiedQuantum 文档 <https://github.com/IAI-USTC-Quantum/UnifiedQuantum/tree/main/docs/source>`_ —— 框架侧的线路构建 / 模拟 / 提交指南
- 类型存根 ``uniqc_cpp.pyi`` 随 wheel 一起发布，IDE 与类型检查器可直接使用

索引
----

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
