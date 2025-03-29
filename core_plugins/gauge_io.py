#!/usr/bin/env python3
import os
import numpy as np
from typing import List

def parse_line(line):
    """解析单行数据并返回元组"""
    items = line.strip().split('\t')
    
    converted = []
    for item in items:
        # 尝试转换为int
        try:
            converted.append(int(item))
            continue
        except ValueError:
            pass
        
        # 尝试转换为float
        try:
            converted.append(float(item))
            continue
        except ValueError:
            pass
        
        # 保持字符串不变，NA转为None
        converted.append(item if item != 'NA' else None)
    
    return tuple(converted)

def parse_file(file_path:str)->List:
    """读取文件并返回包含所有元组的列表
    
    Args:
        file_path (str): 要读取的文件路径
        
    Returns:
        list[tuple]: 包含所有解析后数据的列表
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 跳过空行
            if line.strip():
                data.append(parse_line(line))
    return data

def gather_cutline(data : List, dbu_in_nm : float):
    cutlines = [x[4:8] for x in data]
    arr = np.array(cutlines)
    x_eq = arr[:, 0] == arr[:, 2]
    y_eq = arr[:, 1] == arr[:, 3]
    check = x_eq != y_eq
    success = True
    for i in range(len(check)):
        if not check[i]:
            print(f"cutline check failed {arr[i]}")
            success = False
    assert(success)
    return arr * dbu_in_nm

def get_midpoints_from_cutline(cutlines : np.array)-> np.array:
    return np.column_stack([
        (cutlines[:, 0] + cutlines[:, 2]) / 2, 
        (cutlines[:, 1] + cutlines[:, 3]) / 2  
    ])

def clip_layers_by_cutline(gds_path:str,cutlines : np.array, shape : tuple[float, float], layer_id:int, cell_name:str):
    from klayout_op import clip_layers, subclip_workdir
    xsize, ysize = shape[0] / 2, shape[1] / 2
    start_points = np.column_stack([
        (cutlines[:, 0] + cutlines[:, 2]) / 2 - xsize, 
        (cutlines[:, 1] + cutlines[:, 3]) / 2 - ysize 
    ])
    start_points = [tuple(map(float, row)) for row in start_points]
    clip_layers(gds_path, subclip_workdir(gds_path), layer_id, start_points, shape, cell_name)

    # 
# 使用示例
if __name__ == '__main__':
    file_path = '/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_7.ss'  # 替换为你的实际文件路径
    parsed_data = parse_file(file_path)
    cutlines = gather_cutline(parsed_data, dbu_in_nm = 0.00025)
    clip_layers_by_cutline(
        "/home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas", 
        cutlines, (8, 8), 300, "JDV_M"
    )
    points = get_midpoints_from_cutline(cutlines)
    print(cutlines)
    print(points)
