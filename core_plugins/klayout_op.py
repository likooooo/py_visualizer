#!/usr/bin/env python3
import os
import argparse
import tempfile
import numpy as np
from params_io import *
import klayout.db as pya
from typing import List, Tuple
import matplotlib.pyplot as plt

def get_dbu(oas_file:str="",layout = None):
    if layout is None:
        assert(os.path.exists(oas_file))
        layout = pya.Layout()
        layout.read(oas_file)
    return layout.dbu

def load_shpaes(oas_file, cell_name, layer_id):
    layout = pya.Layout()
    layout.read(oas_file)
    # 获取目标单元格
    top_cell = layout.cell(cell_name) if cell_name else layout.top_cell()
    if not top_cell:
        raise ValueError("未找到指定单元格")
    # 查找目标图层
    layer_index = None
    for li in layout.layer_indices():
        info = layout.get_info(li)
        if info.layer == layer_id and info.datatype == 0:
            layer_index = li
            break
    if layer_index is None:
        raise ValueError(f"未找到图层 {layer_id}/0")

    shapes = top_cell.shapes(layer_index)
    return layout, top_cell, shapes

def save_region_to_file(clipped_region, dbu, cell_name, layer_id, path):
    # 保存结果
    if not clipped_region.is_empty():
        # 创建临时布局
        temp_layout = pya.Layout()
        temp_layout.dbu = dbu
        
        # 创建结果单元格
        result_cell = temp_layout.create_cell(f"{cell_name}")
        result_layer = temp_layout.layer(layer_id, 0)
        # 插入裁剪结果
        for poly in clipped_region.each():
            result_cell.shapes(result_layer).insert(poly)
        
        # 写入文件
        output_file = path
        temp_layout.write(output_file)
        print(f"    已保存: {output_file}")
    else:
        print(f"跳过文件保存, 空裁剪区域: {path}")

# dbu 单位 : um/pixel
def clip_layers(
    oas_file: str, 
    clip_dir: str, 
    layer_id: int, 
    start_points: list[tuple[float, float]], 
    shape: tuple[float, float], 
    cell_name: str = None,
    merge_tolerance: float = 0.0
):
    os.makedirs(clip_dir, exist_ok=True)
    layout, top_cell, shapes = load_shpaes(oas_file, cell_name, layer_id)
    dbu = layout.dbu
    # 将 box 类型转化成 poly
    layer_region = pya.Region()
    layer_region.insert(shapes)
    
    if merge_tolerance > 0:
        layer_region.merge(merge_tolerance)  # 合并相邻多边形
    
    # 准备裁剪区域参数
    width, height = shape
    clip_width_dbu = int(width / dbu)
    clip_height_dbu = int(height / dbu)
    
    # 并行处理每个裁剪区域
    print(f"开始处理 {len(start_points)} 个裁剪区域...")
    for n, (sx, sy) in enumerate(start_points):
        # 计算DBU坐标
        x_dbu = int(sx / dbu)
        y_dbu = int(sy / dbu)
        # 创建裁剪区域
        clip_box = pya.Box(
            pya.Point(x_dbu, y_dbu),
            pya.Point(x_dbu + clip_width_dbu, y_dbu + clip_height_dbu)
        )
        clip_region = pya.Region(clip_box)
        clipped_region = layer_region & clip_region
        save_region_to_file(clipped_region, layout.dbu, top_cell.name, layer_id, os.path.join(clip_dir, f"{n}.oas"))
    print("处理完成！")

def draw_oas_with_holes(oas_file, cell_name, layer_id):
    layout, cell, shapes = load_shpaes(oas_file, cell_name, layer_id)
    
    def plot_points(outer:np.array, color :str = 'r-'):
        outer = outer * layout.dbu
        x = [p[0] for p in outer]
        y = [p[1] for p in outer]
        x.append(x[0])  # 闭合
        y.append(y[0])  # 闭合
        plt.plot(x, y, color)
    from hole_algo import get_outer_and_holes_from_poinst
    for shape in shapes.each():
        if shape.is_polygon():
            poly = shape.polygon
            # 绘制外轮廓
            hull_points = np.array([[p.x, p.y] for p in poly.each_point_hull()])
            outer = hull_points
            holes = []
            # outer, holes = get_outer_and_holes_from_poinst(hull_points)
            plot_points(outer, 'b-')
            for hole in holes:
                plot_points(hole, 'r--')
        elif shape.is_box():
            box = shape.box
            plot_points(np.array([
                [box.left, box.bottom], 
                [box.left, box.top], 
                [box.right, box.top], 
                [box.right, box.bottom]
            ]), 'b-')

    plt.xlabel("X (um)")
    plt.ylabel("Y (um)")
    plt.title(f"Layer {layer_id} from {oas_file}")
    plt.grid(True)
    plt.axis('equal')  

def load_oas_vertexs(oas_file, cell_name, layer_id):
    layout, cell, shapes = load_shpaes(oas_file, cell_name, layer_id)
    
    def plot_points(outer:np.array, color :str = 'r-'):
        outer = outer * layout.dbu
        x = [p[0] for p in outer]
        y = [p[1] for p in outer]
        x.append(x[0])  # 闭合
        y.append(y[0])  # 闭合
        plt.plot(x, y, color)
    from hole_algo import get_outer_and_holes_from_poinst
    poly_vertexs = list()
    hole_vertexs = list()

    debug = False
    for shape in shapes.each():
        if shape.is_polygon():
            poly = shape.polygon
            # 绘制外轮廓
            hull_points = np.array([[p.x, p.y] for p in poly.each_point_hull()], dtype= np.int64)
            outer = hull_points
            holes = []

            # outer, holes = get_outer_and_holes_from_poinst(hull_points)
            # assert(outer.dtype == np.int64)
            # if 0 != len(holes): assert(holes[0].dtype == np.int64)
            poly_vertexs.append(outer)
            hole_vertexs = hole_vertexs + holes
            if debug:
                plot_points(outer, 'b-')
                for hole in holes:
                    plot_points(hole, 'r--')
        elif shape.is_box():
            box = shape.box
            outer = np.array([
                [box.left, box.bottom], 
                [box.left, box.top], 
                [box.right, box.top], 
                [box.right, box.bottom]
            ], dtype= np.int64)
            poly_vertexs.append(outer)
            if debug: plot_points(outer, 'b-')
    if debug:
        plt.xlabel("X (um)")
        plt.ylabel("Y (um)")
        plt.title(f"Layer {layer_id} from {oas_file}")
        plt.grid(True)
        plt.axis('equal')  
        plt.show()
    return poly_vertexs, hole_vertexs

def parse_start_points(s: str) -> List[Tuple[float, float]]:
    """解析起始点字符串，格式为 'x1,y1;x2,y2;...'"""
    points = []
    for pair in s.split(';'):
        x, y = map(float, pair.split(','))
        points.append((x, y))
    return points

def parse_shape(s: str) -> Tuple[float, float]:
    """解析形状字符串，格式为 'width,height'"""
    return tuple(map(float, s.split(',')))

def subclip_workdir(oas_file:str):
    # create dir to save sub-clip
    clip_dir = os.path.join(tempfile.gettempdir(), "simulation")
    clip_dir = os.path.join(clip_dir, os.path.splitext(os.path.basename(oas_file))[0])
    print(f"    subclip workdir is {clip_dir}")
    assert(0 == os.system(f"mkdir -p {clip_dir}"))
    return clip_dir

def main():
    # 创建命令行解析器
    parser = argparse.ArgumentParser(
        description='GDSII文件图层裁剪工具',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 必需参数
    parser.add_argument(
        'oas_file',
        type=str,
        help='输入的GDSII文件路径'
    )
    parser.add_argument(
        'cell_name',
        type=str,
        help='要处理的单元名称'
    )
    parser.add_argument(
        'layer_id',
        type=int,
        help='要裁剪的图层ID'
    )
    
    # 特殊格式参数
    parser.add_argument(
        '--start-points',
        type=str,
        default="",
        help='起始坐标点，格式为"x1,y1;x2,y2;..."',
        metavar='"X,Y;X,Y;..."'
    )
    parser.add_argument(
        '--shape',
        type=str,
        default= "1, 1",
        help='裁剪矩形形状，格式为"width,height"',
        metavar='W,H'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    if "" == args.start_points:
        print(f"    draw layer_{args.layer_id} in {args.oas_file}")
        draw_oas_with_holes(args.oas_file, args.cell_name, args.layer_id)
        plt.show()
        return
        
    # 转换参数格式
    try:
        start_points = parse_start_points(args.start_points)
        shape = parse_shape(args.shape)
    except ValueError as e:
        parser.error(f"参数格式错误: {e}")
    
    workdir = subclip_workdir(args.oas_file)
    key_params = (args.oas_file, args.layer_id, args.cell_name, shape, start_points)
    args_cache = os.path.join(workdir, "info.bin")
    if os.path.exists(args_cache) and args_from_file(filepath=args_cache) == key_params: 
        print("    subclip alread done")
        return
    clip_layers(
        oas_file=args.oas_file,
        clip_dir=workdir,
        layer_id=args.layer_id,
        start_points=start_points,
        shape=shape,
        cell_name=args.cell_name
    )
    args_to_file(key_params, filepath=args_cache)

'''
python klayout_op.py /home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas "JDV_M" 300  \
    --start-points "2307.5, 21765.5;2323.5, 21765.5;2339.5, 21765.5;2355.5, 21765.5" \
    --shape "8, 8" 

python klayout_op.py /tmp/simulation/LG40_PC_CDU_Contour_Mask_L300/0.gds "JDV_M" 300  
'''
if __name__ == '__main__':
    main()