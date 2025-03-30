#!/usr/bin/env python3
import os
import gdspy
import argparse
import tempfile
import numpy as np
from params_io import *
from typing import List, Tuple

import warnings
# 标记整个模块为废弃
warnings.warn(
    "此模块已废弃, 请使用 klayout_op 替代",
    DeprecationWarning,
    stacklevel=2  # 确保警告指向调用方而非本文件
)


def layer_slice(cell, layer, roi : list) -> np.ndarray: # shpae=(n,2)
    """
    按照 ROI 对 layer 进行切片。

    参数：
        cell (gdspy.Cell): 要操作的单元格。
        layer (int): 要切片的 layer 编号。
        roi (list): 切片的 ROI 区域。

    返回：
        gdspy.PolygonSet: 切片后的多边形集合。
    """

    polygons = cell.get_polygons(by_spec=(layer, 0))
    if not polygons: return gdspy.PolygonSet([])
    
    assert(4 == len(roi))
    x1, y1, x2, y2 = roi
    rectangle = gdspy.Rectangle((x1, y1), (x2, y2), layer=layer)
    sliced_polygons = gdspy.boolean(polygons, rectangle, 'and', layer=layer)
    return sliced_polygons

def layer_boolean(cell1, layer1, cell2, layer2, operation):
    """
    对两个 layer 进行布尔运算。

    参数：
        cell1 (gdspy.Cell): 第一个单元格。
        layer1 (int): 第一个 layer 编号。
        cell2 (gdspy.Cell): 第二个单元格。
        layer2 (int): 第二个 layer 编号。
        operation (str): 布尔运算类型，可选 'and'、'or'、'xor'。

    返回：
        gdspy.PolygonSet: 布尔运算后的多边形集合。
    """

    polygons1 = cell1.get_polygons(by_spec=(layer1, 0)) 
    polygons2 = cell2.get_polygons(by_spec=(layer2, 0)) 

    if not polygons1:
        polygons1 = gdspy.PolygonSet([])
    if not polygons2:
        polygons2 = gdspy.PolygonSet([])

    if operation not in ['and', 'or', 'xor']: raise ValueError(f"Invalid operation={operation}. Must be 'and', 'or', or 'xor'.")

    result = gdspy.boolean(polygons1, polygons2, operation, layer=layer1)
    return result

def clip_example():
    cell1 = gdspy.Cell('CELL1')
    cell2 = gdspy.Cell('CELL2')

    rect1 = gdspy.Rectangle((0, 0), (10, 10), layer=1)
    rect2 = gdspy.Rectangle((5, 5), (15, 15), layer=2)
    circle = gdspy.Round((7.5, 7.5), 5, layer=3)

    cell1.add(rect1)
    cell2.add(rect2)
    cell1.add(circle)

    # 按照 ROI 切片 layer 1
    sliced_layer1 = layer_slice(cell1, 1, [2, 2, 8, 8])

    and_result = layer_boolean(cell1, 1, cell2, 2, 'and')
    or_result = layer_boolean(cell1, 1, cell2, 2, 'or')
    xor_result = layer_boolean(cell1, 1, cell2, 2, 'xor')

    # 创建一个新的单元格来显示结果
    result_cell = gdspy.Cell('RESULT')
    result_cell.add(sliced_layer1)
    result_cell.add(and_result)
    result_cell.add(or_result)
    result_cell.add(xor_result)

    # 将结果保存到 GDS 文件中
    gdspy.write_gds('layer_operations.gds', unit=1e-6, precision=1e-9)
    
def clip_layers(gds_file:str, clip_dir:str,layer_id:int, start_points : list[tuple[float, float]],  shape: tuple[float, float], cell_index:int = 0):
    # load cell
    lib = gdspy.GdsLibrary()
    lib.read_gds(gds_file) 
    top_cells = lib.top_level()
    if not top_cells: raise ValueError("文件中未找到顶层单元。")
    
    # load layer
    top_cell = top_cells[cell_index]
    polygons = top_cell.get_polygons(by_spec=(layer_id, 0))
    if not polygons: raise ValueError(f"层 {layer_id} 未找到多边形。")
    
    # clip
    xsize, ysize = shape
    n = 0
    for sx, sy in start_points:
        rectangle = gdspy.Rectangle((sx, sy), (sx + xsize, sy + ysize), layer=-1)
        sliced_polygons = gdspy.boolean(polygons, rectangle, 'and', layer=layer_id)
        if None is sliced_polygons:
            print(f"empty clip from {sx, sy}")
            continue
        result_cell = gdspy.Cell(f'clip{n}')
        result_cell.add(sliced_polygons)
        temp_lib = gdspy.GdsLibrary()
        temp_lib.add(result_cell)
        temp_lib.unit = lib.unit
        temp_lib.write_gds(os.path.join(clip_dir, f"{n}.gds"))
        n = n + 1

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


def subclip_workdir(gds_file:str):
    # create dir to save sub-clip
    clip_dir = os.path.join(tempfile.gettempdir(), "simulation")
    clip_dir = os.path.join(clip_dir, os.path.splitext(os.path.basename(gds_file))[0])
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
        'gds_file',
        type=str,
        help='输入的GDSII文件路径'
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
        required=True,
        help='起始坐标点，格式为"x1,y1;x2,y2;..."',
        metavar='"X,Y;X,Y;..."'
    )
    parser.add_argument(
        '--shape',
        type=str,
        required=True,
        help='裁剪矩形形状，格式为"width,height"',
        metavar='W,H'
    )
    
    # 可选参数
    parser.add_argument(
        '--cell-index',
        type=int,
        default=0,
        help='要处理的单元索引（默认为0）'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 转换参数格式
    try:
        start_points = parse_start_points(args.start_points)
        shape = parse_shape(args.shape)
    except ValueError as e:
        parser.error(f"参数格式错误: {e}")
    
    
    workdir = subclip_workdir(args.gds_file)
    key_params = (args.gds_file, args.layer_id, args.cell_index, shape, start_points)
    args_cache = os.path.join(workdir, "info.bin")
    if os.path.exists(args_cache) and args_from_file(filepath=args_cache) == key_params: 
        print("    subclip alread done")
        return
    clip_layers(
        gds_file=args.gds_file,
        clip_dir=workdir,
        layer_id=args.layer_id,
        start_points=start_points,
        shape=shape,
        cell_index=args.cell_index
    )
    args_to_file(key_params, filepath=args_cache)

'''
python gds_op.py /home/like/doc/YuWei/gds/gds/case10.gds 8888 \
    --start-points "-0.15,-0.15; 0,  -0.15; -0.075, -0.075" \
    --shape "0.15, 0.15" \
    --cell-index 0
'''
if __name__ == '__main__':
    main()