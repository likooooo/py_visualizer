#!/usr/bin/env python3
import numpy as np

def svd(A, y):
    # print(f"* A is\n{A}")
    # print(f"* Y is\n{y}")
    # SVD 分解
    U, S, VT = np.linalg.svd(A, full_matrices=False)
    
    threshold = 1e-10  # 设定阈值
    Sigma_inv = np.diag([1/s if s > threshold else 0 for s in S])
    # 用伪逆求解 x 
    # x = (A^+) .* y
    x = VT.T @ Sigma_inv @ U.T @ y
    # print(f"    optimize S={S} condition-number is {S.max()/ S.min()}")
    return x.tolist()