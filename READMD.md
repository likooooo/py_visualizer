# py_visualizer

py_visualizer 支持 c++ 调用 matplotlib 进行可视化。

1. 环境配置
``` shell
sudo apt install libboost-all-dev
pip install numpy=1.26.4 
sudo apt-get install python3-tk
pip install matplotlib
```

2. 常见问题
-  报错 1：
``` shell
A module that was compiled using NumPy 1.x cannot be run in
NumPy 2.2.0 as it may crash. To support both 1.x and 2.x
versions of NumPy, modules must be compiled with NumPy 2.0.
Some module may need to rebuild instead e.g. with 'pybind11>=2.12'.

If you are a user of the module, the easiest solution will be to
downgrade to 'numpy<2' or try to upgrade the affected module.
We expect that some modules will need time to support NumPy 2.
```
python 的 numpy 和 boost::python::numpy 不兼容 

- 报错 2：
```shell
 UserWarning: FigureCanvasAgg is non-interactive, and thus cannot be shown
```
安装 python3-tk, 或者安装 PyQt 并参考 [stackoverflow](https://stackoverflow.com/questions/77507580/userwarning-figurecanvasagg-is-non-interactive-and-thus-cannot-be-shown-plt-sh)