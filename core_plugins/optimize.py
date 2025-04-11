#!/usr/bin/env python3
import numpy as np
from scipy import sparse
import osqp

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


def unconstrained_optimization(P, q):
    # Step 1: 对 P 进行 SVD 分解
    U, Sigma, VT = np.linalg.svd(P)  # 返回 VT = U^T，因为 P 是对称矩阵

    # Step 2: 计算伪逆 Sigma^+
    Sigma_pinv = np.zeros_like(P, dtype=float)  # 初始化正确形状的矩阵
    rank = np.sum(Sigma > 1e-10)               # 计算非零奇异值的数量
    Sigma_pinv[:rank, :rank] = np.diag(1 / Sigma[:rank])

    # Step 3: 计算 P 的伪逆 P^+ = U @ Sigma^+ @ V^T
    P_pinv = U @ Sigma_pinv @ VT

    # Step 4: 计算最优解 x^* = -P^+ q
    x_opt = -P_pinv @ q
    x_norm = x_opt / np.linalg.norm(x_opt)
    return x_norm.tolist()

def psd_correct_diagonal(P, epsilon=1e-6):
    '''
    为什么需要对角线修正？
        1. 保证数值稳定性：

        如果 P 矩阵的对角线元素过小（甚至为 0），可能导致矩阵非正定或条件数过大，引发数值问题。

        通过对角线修正（增加 erc），可以强制 P 矩阵满足正定性要求。

        2. 处理用户输入的 P 矩阵：

        用户提供的 P 矩阵可能有数值误差或非正定的情况。

        例如，P 可能是通过数据估计得到的协方差矩阵，理论上半正定，但实际计算中可能因数值误差导致微小负特征值。

        3. 正则化（Regularization）：

        修正量 erc 类似于正则化项，通过增加对角线值，可以避免过拟合或病态问题。
    '''
    n = P.shape[0]
    P_corrected = P.copy()
    P_corrected += np.eye(n) * epsilon  # 对角线增加 epsilon
    return P_corrected

def optimization_with_kkt(P, q, A, b):
    P = P * 1e2
    P = psd_correct_diagonal(P, 1e-6)
    # Step 1: 对 A 进行SVD分解
    U, Sigma, VT = np.linalg.svd(A)
    rank_A = np.sum(Sigma > 1e-10)  # 约束矩阵的秩
    m, n = A.shape

    # Step 2: 特解 x_particular = A^+ b
    Sigma_pinv = np.zeros((n, m))
    Sigma_pinv[:rank_A, :rank_A] = np.diag(1 / Sigma[:rank_A])
    A_pinv = VT.T @ Sigma_pinv @ U.T
    x_particular = A_pinv @ b

    # Step 3: 计算零空间基（null space basis）
    if rank_A < n:
        null_space_basis = VT[rank_A:].T  # 零空间基向量 (n x (n-rank_A))
    else:
        raise ValueError(f"约束矩阵 A 行满秩，无自由优化变量！ rank_A={rank_A}, n={n}")

    # Step 4: 构造降阶问题 P_reduced * alpha = -q_reduced
    P_reduced = null_space_basis.T @ P @ null_space_basis  # 形状 (n-rank_A, n-rank_A)
    q_reduced = (q + P @ x_particular).T @ null_space_basis  # 形状 (n-rank_A,)

    # Step 5: 解 alpha = -P_reduced^{-1} q_reduced
    if P_reduced.size > 0:
        alpha = -np.linalg.solve(P_reduced, q_reduced)  # 数值稳定的求解
    else:
        alpha = np.array([])

    # Step 6: 组合解 x = x_particular + null_space_basis * alpha
    if rank_A < n:
        x_opt = x_particular + null_space_basis @ alpha
    else:
        x_opt = x_particular  # 无自由变量时，特解是唯一解
    # x_norm = x_opt / np.linalg.norm(x_opt)
    return x_opt.tolist()

def optimizeation_osqp(P, q, A, l, u):
    P = P / 2

    P = P * 1e2
    P = psd_correct_diagonal(P, 1e-6)
    P = sparse.csc_matrix(P) 
    A = sparse.csc_matrix(A) 

    # 创建并设置问题
    prob = osqp.OSQP()
    prob.setup(P, q, A, l, u, verbose=False)

    # 求解问题
    res = prob.solve()

    # 正确获取向量形式的优化结果
    optimal_vector = res.x  # 这是一个n维numpy数组

    print("优化结果向量:")
    print(optimal_vector)
    print(f"类型: {type(optimal_vector)}, 形状: {optimal_vector.shape}\n")
    return optimal_vector.tolist()

def test():
    # 问题数据 - 3变量示例
    n = 3  # 变量个数
    m = 4  # 约束个数

    # 目标函数: 最小化 0.5x^T P x + q^T x
    P = sparse.csc_matrix([[4., 1., 0.], 
                        [1., 2., 0.], 
                        [0., 0., 1.]])  # 必须是正定或半正定矩阵
    q = np.array([1., 1., 0.5])

    # 约束条件: l <= A x <= u
    A = sparse.csc_matrix([[1., 1., 0.],   # x1 + x2 >= 1
                        [1., 0., 0.],    # x1 <= 10
                        [0., 1., 0.],    # x2 <= 10
                        [0., 0., 1.]])   # x3 = 5 (等式约束)

    l = np.array([1., -np.inf, -np.inf, 5.])
    u = np.array([np.inf, 10., 10., 5.])

    # 创建并设置问题
    prob = osqp.OSQP()
    prob.setup(P, q, A, l, u, verbose=False)

    # 求解问题
    res = prob.solve()

    # 正确获取向量形式的优化结果
    optimal_vector = res.x  # 这是一个n维numpy数组

    print("优化结果向量:")
    print(optimal_vector)
    print(f"类型: {type(optimal_vector)}, 形状: {optimal_vector.shape}\n")

    # 按变量访问结果
    print(f"x1 = {optimal_vector[0]:.4f}")
    print(f"x2 = {optimal_vector[1]:.4f}")
    print(f"x3 = {optimal_vector[2]:.4f}\n")

    # 验证约束
    Ax = A.dot(optimal_vector)
    print("约束验证:")
    for i in range(m):
        print(f"约束{i+1}: {l[i]:.2f} <= {Ax[i]:.2f} <= {u[i]:.2f}")

    # 目标函数值验证
    obj_val = 0.5 * optimal_vector @ P @ optimal_vector + q @ optimal_vector
    print(f"\n计算的目标值: {obj_val:.4f}")
    print(f"求解器报告的目标值: {res.info.obj_val:.4f}")