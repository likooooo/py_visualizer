#!/usr/bin/env python3
import numpy as np

def test():
    # 生成数据
    n, m = 100, 3
    X = np.random.randn(n, m)  # 设计矩阵 (n × m)
    a_true = np.array([1.5, -2.0, 0.5])  # 真实系数
    y = X @ a_true + 0.1 * np.random.randn(n)  # 带噪声的观测值

    print(y.shape)

    # SVD 分解
    U, Sigma, VT = np.linalg.svd(X, full_matrices=False)
    Sigma_inv = np.diag(1.0 / Sigma)  # 伪逆 Σ⁺

    # 计算最小二乘解
    a_ls = VT.T @ Sigma_inv @ U.T @ y

    print("真实系数:", a_true)
    print("估计系数:", a_ls)

def svd(A, y):
    # print(f"* A is\n{A}")
    # print(f"* Y is\n{y}")
    # SVD 分解
    U, Sigma, VT = np.linalg.svd(A, full_matrices=False)
    Sigma_inv = np.diag(1.0 / Sigma)  # 伪逆 Σ⁺
    a_ls = VT.T @ Sigma_inv @ U.T @ y
    return a_ls.tolist()