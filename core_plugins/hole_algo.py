#!/usr/bin/env python3
import numpy as np
from typing import Tuple, List

# 类型别名
Point = np.ndarray  # shape=(2,) [x, y]
Edge = np.ndarray    # shape=(2, 2) [[x1,y1], [x2,y2]]
Polygon = np.ndarray # shape=(N, 2) [[x1,y1], [x2,y2], ...]

def edge_length(edge: Edge) -> float:
    """计算边长"""
    return np.linalg.norm(edge[1] - edge[0])

def cross_product(p1: Point, p2: Point) -> float:
    """二维叉积"""
    return p1[0] * p2[1] - p1[1] * p2[0]

def is_point_on_line(p: Point, edge: Edge) -> bool:
    """判断点是否在边上"""
    v1 = p - edge[0]
    v2 = edge[1] - edge[0]
    cp = cross_product(v2, v1)
    
    x_in_range = (min(edge[0][0], edge[1][0]) <= p[0] <= max(edge[0][0], edge[1][0]))
    y_in_range = (min(edge[0][1], edge[1][1]) <= p[1] <= max(edge[0][1], edge[1][1]))
    
    return np.isclose(cp, 0) and x_in_range and y_in_range

def is_colinear(edge1: Edge, edge2: Edge) -> bool:
    """判断两条边是否共线"""
    # 快速排除法：边方向不一致
    dir1 = edge1[1] - edge1[0]
    dir2 = edge2[1] - edge2[0]
    if not np.isclose(cross_product(dir1, dir2), 0):
        return False
    
    # 检查三点共线
    return is_point_on_line(edge2[0], edge1) and is_point_on_line(edge2[1], edge1)

def is_same_direction(edge1: Edge, edge2: Edge) -> bool:
    """判断两条边方向是否相同"""
    vec1 = edge1[1] - edge1[0]
    vec2 = edge2[1] - edge2[0]
    return np.dot(vec1, vec2) > 0  # 向量点积大于0表示同向

def detect_holes(points: Polygon) -> Tuple[Polygon, List[Polygon]]:
    """
    检测多边形中的孔洞
    返回: (外轮廓, 孔洞列表)
    """
    points = np.asarray(points, dtype=np.float64)
    pos_info = {tuple(p): i for i, p in enumerate(points)}  # 点坐标到索引的映射
    consider_edges = []  # 待比较的边
    holes = []          # 检测到的孔洞
    anchors = []        # 孔洞锚点索引
    
    for i in range(1, len(points)):
        new_edge = np.array([points[i-1], points[i]])
        
        # 反向检查历史边
        for j in range(len(consider_edges)-1, -1, -1):
            edge = consider_edges[j]
            
            if is_colinear(new_edge, edge) and not is_same_direction(new_edge, edge):
                if (is_point_on_line(new_edge[0], edge) or 
                    is_point_on_line(new_edge[1], edge) or
                    is_point_on_line(edge[0], new_edge) or
                    is_point_on_line(edge[1], new_edge)):
                    
                    # 确定孔洞范围
                    hole_start = pos_info[tuple(edge[1])]
                    hole_end = i - 1
                    
                    # 提取孔洞点
                    hole = points[hole_start : hole_end + 1]
                    
                    # 验证孔洞有效性（顺时针方向）
                    winding = 0
                    for k in range(1, len(hole)):
                        if k >= 2:
                            v1 = hole[k-1] - hole[k-2]
                            v2 = hole[k] - hole[k-1]
                            winding += 1 if cross_product(v1, v2) < 0 else -1
                    
                    if winding < 0:  # 有效孔洞（顺时针）
                        holes.append(hole)
                        anchors.append((hole_start, hole_end))
                        consider_edges = consider_edges[:j+1]  # 移除已处理的边
                        break
        
        consider_edges.append(new_edge)
    
    # 处理外轮廓（移除孔洞部分）
    outer = points.copy()
    for start, end in sorted(anchors, reverse=True):
        outer = np.delete(outer, slice(start, end+1), axis=0)
    
    return outer, holes


def detect_holes_v1(points: Polygon) -> Tuple[Polygon, List[Polygon]]:
    outer = points
    holes = list()
    for i in range(len(points) - 1):
        for j in range(len(points) - 1, i, -1):
            if (points[i] == points[j]).all():
                outer = np.concatenate([points[:i], points[j:]])
                temp = points
                while True:
                    temp, hole = detect_holes(temp)
                    if 0 == len(hole): break
                    holes = holes + hole 
    return outer, holes
def get_outer_and_holes_from_poinst(square : np.array):
    holes = list()
    outer = square
    assert(square.shape[1] == 2) # point check
    outer, holes = detect_holes_v1(outer)
        
    # while True:
        # outer, hole = detect_holes(outer)
        # if 0 == len(hole): break
        # holes = holes + hole 
    return outer, holes 

if __name__ == "__main__":
    # 示例多边形（外轮廓+孔洞）
    square = np.array([
        # [0,0], [10,0], [10,10], [0,10], [0,0],  # 外轮廓闭合
        # [2,2], [8,2], [8,8], [2,8], [2,2]        # 孔洞（顺时针）
        [2325.55000, 21765.50000],
        [2325.55000, 21766.00000],
        [2325.85000, 21766.00000],
        [2325.85000, 21765.90000],
        [2325.65000, 21765.90000],
        [2325.65000, 21765.80000],
        [2325.85000, 21765.80000],
        [2325.85000, 21765.70000],
        [2325.65000, 21765.70000],
        [2325.65000, 21765.60000],
        [2325.85000, 21765.60000],
        [2325.85000, 21766.00000],
        [2325.95000, 21766.00000],
        [2325.95000, 21765.50000],
    ])
    outer, holes = get_outer_and_holes_from_poinst(square)
    print("外轮廓:")
    print(outer)
    print("\n检测到的孔洞:")
    for i, hole in enumerate(holes):
        print(f"孔洞 {i+1}:")
        print(hole)
    import matplotlib.pyplot as plt
    def plot_polygon(outer: Polygon, holes: List[Polygon]):
        plt.figure()
        
        # 绘制外轮廓
        plt.plot(outer[:,0], outer[:,1], 'b-', label='Outer')
        plt.fill(outer[:,0], outer[:,1], 'b', alpha=0.1)
        
        # 绘制孔洞
        for i, hole in enumerate(holes):
            plt.plot(hole[:,0], hole[:,1], 'r--', label=f'Hole {i+1}')
            plt.fill(hole[:,0], hole[:,1], 'w')  # 白色填充表示挖空
        
        plt.axis('equal')
        plt.legend()
        plt.show()

    plot_polygon(outer, holes)