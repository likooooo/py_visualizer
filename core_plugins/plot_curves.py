#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt

def plot_curves(lines, start_x=None, step_x=None, legends=None, types=None, sample_rate=1.0):
    """
    绘制曲线。

    参数：
        lines (list of list): 曲线数据的列表，其中每个子列表表示一条曲线。
        start_x (list, optional): 长度为 n 的列表，表示每条曲线的起始点 x。默认为 None。
        step_x (list, optional): 长度为 n 的列表，表示每条曲线的 x 步长。默认为 None。
        legends (list, optional): 长度为 n 的列表，表示每条曲线的图例。默认为 None。
        types (list, optional): 长度为 n 的列表，表示每条曲线的绘制方式。默认为 None。
        sample_rate (float, optional): 0-1 之间的浮点数，表示采样率。默认为 1.0 (不采样)。
    """

    n = len(lines)  # 曲线的数量

    if start_x is None:
        start_x = [0] * n
    if step_x is None:
        step_x = [1] * n
    if legends is None:
        legends = [f'Curve {i}' for i in range(n)]
    if types is None:
        types = ['-'] * n

    for i in range(n):
        y = np.array(lines[i])  # 将list转化为numpy array
        m = len(y) # 获取当前曲线的点数
        x = np.array([start_x[i] + j * step_x[i] for j in range(m)])

        if sample_rate < 1.0:
            sample_size = int(m * sample_rate)
            if sample_size < 2:
                sample_size = 2  # 确保采样后的点数至少为 2
            sample_indices = np.random.choice(m, size=sample_size, replace=False)
            sample_indices.sort()
            x = x[sample_indices]
            y = y[sample_indices]

        plt.plot(x, y, types[i], label=legends[i])

    plt.legend(loc='upper right')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Curves')
    plt.grid(True)
    plt.show()