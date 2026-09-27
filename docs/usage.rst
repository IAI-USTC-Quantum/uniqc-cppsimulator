安装与构建
==========

安装
----

.. code-block:: bash

   pip install uniqc-cppsimulator

提供 Linux / Windows / macOS 的 cp310–cp314 预编译 wheel；其余平台自动从
sdist 源码编译，需要满足下方"源码构建要求"。

安装后 import 名为 ``uniqc_cpp``（分发名 ``uniqc-cppsimulator``）。

快速上手
--------

.. code-block:: python

   import uniqc_cpp

   sim = uniqc_cpp.StatevectorSimulator()
   sim.init_n_qubit(2)
   sim.hadamard(0)
   sim.cnot(0, 1)
   print(sim.pmeasure([0, 1]))  # Bell 态: [0.5, 0, 0, 0.5]

完整 API 见 :doc:`api_uniqc_cpp` 与类型存根 ``uniqc_cpp.pyi``。

多线程
------

内核提供**全局**多线程开关与线程数控制（默认关闭，单线程，与历史行为一致）：

.. code-block:: python

   import uniqc_cpp

   uniqc_cpp.set_num_threads(8)          # 全局线程数（>=1，超出硬件并发数会被截断）
   uniqc_cpp.set_parallel_enabled(True)  # 打开全局开关；False 时任何调用都单线程执行
   print(uniqc_cpp.get_num_threads(), uniqc_cpp.is_parallel_enabled())

两个设置均为进程级全局状态，作用于所有模拟器实例，可在任意时刻切换。门操作
（含受控门）结果与单线程**逐位一致**；仅概率类读出（``pmeasure`` / ``get_prob``）
因浮点求和顺序不同存在 ~1e-15 量级的差异。小规模态（< 2^14 幅度）自动回落单线程。

想看这个内核在 UnifiedQuantum 框架里如何被调用，见 `UnifiedQuantum 文档的本地模拟章节 <https://github.com/IAI-USTC-Quantum/UnifiedQuantum/blob/main/docs/source/1_basic_usage/simulation.md>`_。

源码构建要求
------------

- CMake >= 3.22
- 支持 C++17 的编译器（MSVC / gcc / clang）
- pybind11（构建隔离模式下由 ``pyproject.toml`` 自动提供）
- 第三方库 `fmt <https://fmt.dev/>`_ 已 vendored 在 ``UniqcCpp/Thirdparty/``，无需额外安装

.. code-block:: bash

   git clone https://github.com/IAI-USTC-Quantum/uniqc-cppsimulator.git
   cd uniqc-cppsimulator
   pip install .

没有系统级编译工具链时，可用用户级工具链（如 conda-forge 的
``gxx_linux-64`` + ``cmake`` + ``ninja``，经 micromamba 安装到 ``~/.local``）：

.. code-block:: bash

   export PATH="$HOME/.local/share/micromamba/envs/cpp/bin:$PATH"
   export CC=x86_64-conda-linux-gnu-gcc CXX=x86_64-conda-linux-gnu-g++
   uv pip install --python .venv-bench/bin/python --reinstall --no-deps .

测试
----

.. code-block:: bash

   # Python 绑定测试
   pytest tests/

   # C++ 原生测试
   cmake -S . -B build-cpp -DCMAKE_BUILD_TYPE=Release \
     -Dpybind11_DIR="$(python -c 'import pybind11; print(pybind11.get_cmake_dir())')"
   cmake --build build-cpp --config Release
   ./build-cpp/bin/Release/UnifiedQuantumTest   # Windows: .\build-cpp\bin\Release\UnifiedQuantumTest.exe

想评估性能或与其它模拟器对比，见 :doc:`benchmark` 与 :doc:`includes/benchmark-results`。

文档构建
--------

文档源在 ``docs/``（本站），构建依赖见 ``docs/requirements.txt``；因为要
autodoc 导入 ``uniqc_cpp`` 与 ``benchmark``，还需安装扩展本体：

.. code-block:: bash

   uv venv .venv-docs --python 3.12
   uv pip install --python .venv-docs -r docs/requirements.txt .
   .venv-docs/bin/python -m sphinx -b html docs docs/_build/html
   # Windows: .venv-docs\Scripts\python -m sphinx -b html docs docs\_build\html

README / CHANGELOG / 基准报告等 markdown 由 ``docs/prepare.py`` 在构建开始时
自动拷入 ``docs/includes/``（生成目录，不入库）；也可以单独运行
``python docs/prepare.py``。推送到 ``main`` 后由 GitHub Actions 自动发布到
GitHub Pages。

相关页面
--------

- :doc:`index` —— 站点导航与项目定位
- :doc:`benchmark` —— 基准测试套件的使用方法
- :doc:`includes/benchmark-methodology` —— 测量方法学、线程模型与扩展指南
- :doc:`includes/changelog` —— 版本历史（Keep a Changelog 格式）
- :doc:`api_benchmark` —— ``benchmark`` Python 包的 API 参考
