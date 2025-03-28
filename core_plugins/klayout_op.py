import os
import argparse
import tempfile
import numpy as np
from params_io import *
import klayout.db as pya
from typing import List, Tuple

# dbu 单位 : um/pixel
def clip_layers(
    gds_file: str, 
    clip_dir: str, 
    layer_id: int, 
    start_points: list[tuple[float, float]], 
    shape: tuple[float, float], 
    cell_name: str = None,
    merge_tolerance: float = 0.0
):
    """
    高性能版图层裁剪（适用于大文件）
    
    参数:
        gds_file: 输入GDS文件路径
        clip_dir: 输出目录路径
        layer_id: 目标图层号
        start_points: 裁剪起始点列表 [(x1,y1), (x2,y2), ...]
        shape: 裁剪区域尺寸 (width, height)
        cell_name: 目标单元格名称（None表示第一个顶层单元格）
        merge_tolerance: 多边形合并容差（单位：DBU）
    """
    # 创建输出目录
    os.makedirs(clip_dir, exist_ok=True)
    
    # 加载布局文件
    layout = pya.Layout()
    layout.read(gds_file)
    dbu = layout.dbu
    
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
    
    # 预加载并合并图层所有多边形（关键优化）
    print("正在合并图层多边形...")
    layer_region = pya.Region()
    shapes = top_cell.shapes(layer_index)
    layer_region.insert(shapes)  # 批量插入提升性能
    
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
        
        # 执行布尔裁剪
        clipped_region = layer_region & clip_region
        
        # 保存结果
        if not clipped_region.is_empty():
            # 创建临时布局
            temp_layout = pya.Layout()
            temp_layout.dbu = dbu
            
            # 创建结果单元格
            result_cell = temp_layout.create_cell(f"clip_{n}")
            result_layer = temp_layout.layer(layer_id, 0)
            
            # 插入裁剪结果
            for poly in clipped_region.each():
                result_cell.shapes(result_layer).insert(poly)
            
            # 写入文件
            output_file = os.path.join(clip_dir, f"clip_{n}.gds")
            temp_layout.write(output_file)
            print(f"已保存: {output_file}")
        else:
            print(f"空裁剪区域: {sx:.3f}, {sy:.3f}")

    print("处理完成！")

            
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
python klayout.py /home/like/doc/YuWei/gds/gds/case10.gds 8888 \
    --start-points "-0.15,-0.15; 0,  -0.15; -0.075, -0.075" \
    --shape "0.15, 0.15" \
    --cell-index 0
'''
if __name__ == '__main__':
    main()