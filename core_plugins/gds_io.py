#!/usr/bin/env python3
import gdspy
import matplotlib.pyplot as plt
import numpy as np

def find_duplicates(points):
    """查找列表中的重复点及其索引。"""
    seen = {}
    duplicates = []
    for i, point in enumerate(map(tuple, points)):
        if point in seen:
            duplicates.append((seen[point], i))
        else:
            seen[point] = i
    return duplicates

def extract_single_hole(polygon_points):
    """递归提取多边形中的孔。"""
    duplicates = find_duplicates(polygon_points)
    if 0 == len(duplicates):
        return (polygon_points, None)  

    holes = None
    outer_polygon = polygon_points.copy()
    for start, end in duplicates:
        outer_polygon = np.concatenate([outer_polygon[:start], outer_polygon[end + 1:]])
        sub_poly = polygon_points[start + 1:end]
        a, b = extract_single_hole(sub_poly)
        # assert(b == None)
        holes = a
        # 从外轮廓中移除孔的部分
    return  (outer_polygon, np.array(holes))

def plot_gds(gds_file):
    # 读取GDS文件
    lib = gdspy.GdsLibrary()
    lib.read_gds(gds_file) 
    dbu = lib.unit
    print(f"gds dbu={dbu}")
    # 获取顶层单元
    top_cells = lib.top_level()
    if not top_cells:
        raise ValueError("文件中未找到顶层单元。")
    top_cell = top_cells[0]

    # 提取所有多边形（包括路径转换后的）
    all_polygons = top_cell.get_polygons(by_spec=True)

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 10))

    # 定义不同层的颜色
    layer_colors = {
        0: "red",
        1: "blue",
        2: "green",
        3: "purple",
        # 按需添加更多层
    }

    # 绘制每个多边形
    color_id = 0
    for (layer, datatype), polygons in all_polygons.items():
        color = layer_colors.get(color_id, "black")
        print(f"load layer={layer} with color={color}")
        for polygon in polygons:
            outer, hole = extract_single_hole(polygon)
            poly = plt.Polygon(outer, closed=True, edgecolor=color, fill=False, linewidth=0.5)
            ax.add_patch(poly)
            if hole is not None:
                poly = plt.Polygon(hole, closed=True, edgecolor=color, fill=False, linewidth=0.5)
                ax.add_patch(poly)
        color_id = color_id + 1

    # 设置坐标轴和比例
    ax.autoscale()
    plt.axis("equal")  # 保持纵横比一致
    plt.xlabel("X (μm)")
    plt.ylabel("Y (μm)")
    plt.title("GDSII")

    # 添加图例（按层）
    handles = [
        plt.Line2D([0], [0], color=color, label=f"Layer {layer}", linewidth=2)
        for layer, color in layer_colors.items() if layer in all_polygons
    ]
    plt.legend(handles=handles, loc="best")

    plt.show()

if __name__ == "__main__":
    plot_gds("/mnt/c/Users/like/Desktop/gds/case9.gds")
