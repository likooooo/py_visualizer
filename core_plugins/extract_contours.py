#!/usr/bin/env python3
import numpy as np
import cv2
import matplotlib.pyplot as plt

def find_and_plot_contours(float_array, threshold, retrieve_mode='tree'):
    """
    提取浮点矩阵的所有轮廓(包含内轮廓)并可视化
    
    参数:
        float_array: numpy.ndarray - 输入的浮点数矩阵(任意值范围)
        threshold: float - 轮廓提取的绝对阈值(与输入矩阵同值域)
        retrieve_mode: str - 轮廓检索模式 ('tree'或'list')
            'tree' - 建立轮廓层级关系
            'list' - 提取所有轮廓不建立层级
            
    返回:
        contours: 检测到的轮廓列表
        hierarchy: 轮廓层级关系(当retrieve_mode='tree'时)
        并显示可视化结果
    """
    # 确保输入是numpy数组
    if not isinstance(float_array, np.ndarray):
        float_array = np.array(float_array)
    
    # 计算数据的实际范围
    data_min = float_array.min()
    data_max = float_array.max()
    data_range = data_max - data_min
    
    # 将阈值映射到0-255范围(用于OpenCV处理)
    thresh_value = int(255 * (threshold - data_min) / data_range) if data_range > 0 else 0
    
    # 将浮点数组归一化到0-255范围(保持原始分布)
    if data_range > 0:
        normalized = ((float_array - data_min) * 255 / data_range).astype(np.uint8)
    else:
        normalized = np.zeros_like(float_array, dtype=np.uint8)
    
    # 应用阈值
    _, binary = cv2.threshold(normalized, thresh_value, 255, cv2.THRESH_BINARY)
    
    # 选择轮廓检索模式
    if retrieve_mode.lower() == 'tree':
        mode = cv2.RETR_TREE
    else:
        mode = cv2.RETR_LIST
    
    # 查找所有轮廓(包含内轮廓)
    contours, hierarchy = cv2.findContours(binary, mode, cv2.CHAIN_APPROX_SIMPLE)
    
    # 创建可视化
    plt.figure(figsize=(15, 6))
    
    # 原始图像
    plt.subplot(1, 3, 1)
    plt.imshow(float_array, cmap='gray')
    plt.colorbar()
    plt.title(f'Original Array\nRange: [{data_min:.2f}, {data_max:.2f}]')
    
    # 二值化图像
    plt.subplot(1, 3, 2)
    plt.imshow(binary, cmap='gray')
    plt.title(f'Binary Image\nThreshold: {threshold:.2f}')
    
    # 带所有轮廓的图像
    plt.subplot(1, 3, 3)
    plt.imshow(float_array, cmap='gray')
    
    # 为不同层级轮廓使用不同颜色
    colors = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,0,1), (0,1,1)]
    
    for i, contour in enumerate(contours):
        color = colors[i % len(colors)]
        # 绘制轮廓
        plt.plot(contour[:, 0, 0], contour[:, 0, 1], color=color, linewidth=2)
        # 标记轮廓序号
        if len(contour) > 0:
            centroid = np.mean(contour[:, 0, :], axis=0)
            plt.text(centroid[0], centroid[1], str(i), color='white', 
                    fontsize=8, ha='center', va='center')
    
    plt.title(f'All Contours (count={len(contours)})')
    plt.colorbar()
    
    plt.tight_layout()
    plt.show()
    
    return contours, hierarchy

# 使用示例 - 测试不同值范围的输入
if __name__ == "__main__":
    # 示例1: 值范围在0-1之外的矩阵
    data1 = np.random.randn(100, 100)  # 标准正态分布(有正有负)
    print("测试数据1 - 值范围:", data1.min(), data1.max())
    find_and_plot_contours(data1, threshold=0.5, retrieve_mode='tree')
    
    # 示例2: 大值范围矩阵
    data2 = np.random.uniform(100, 200, (100, 100))  # 100-200范围
    print("测试数据2 - 值范围:", data2.min(), data2.max())
    find_and_plot_contours(data2, threshold=150, retrieve_mode='list')
    
    # 示例3: 全相同值矩阵(边界情况)
    data3 = np.full((50, 50), 42.0)  # 所有值相同
    print("测试数据3 - 值范围:", data3.min(), data3.max())
    find_and_plot_contours(data3, threshold=42, retrieve_mode='tree')