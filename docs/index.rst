uniqc-cppsimulator 文档
========================

UnifiedQuantum 的 C++ 量子线路模拟内核，独立发版，通过 pybind11 暴露为
**``uniqc_cpp``** Python 扩展模块：

- ``StatevectorSimulator`` —— 态矢量模拟器（最多 30 量子比特）
- ``DensityOperatorSimulator`` —— 密度算符模拟器（最多 10 量子比特，支持噪声通道）

.. toctree::
   :maxdepth: 2
   :caption: 目录

   usage
   benchmark
   api_benchmark
   api_uniqc_cpp

常用入口
--------

- :doc:`usage` —— 安装、源码构建与测试
- :doc:`benchmark` —— 跨模拟器 CPU 基准套件的使用方法
- :doc:`api_benchmark` —— ``benchmark`` 包 API 参考
- :doc:`api_uniqc_cpp` —— ``uniqc_cpp`` 扩展 API 参考

其它资料
--------

- `README <https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator>`_ —— 含基准结果摘要
- `基准详情与图表 <../doc/benchmark.md>`_ —— doc/benchmark.md，随 report 子命令生成
- 类型存根 ``uniqc_cpp.pyi`` 随 wheel 一起发布，IDE 与类型检查器可直接使用

索引
----

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
