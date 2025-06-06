#!/usr/bin/env python3
import os
import numpy as np
from typing import TypeAlias, List, Tuple
from klayout_op import *

def parse_line(line:str) ->Tuple :
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

def read_gauge_file(file_path:str)->List[Tuple]:
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

def nm_to_dbu(nm, dbu): return int(nm * 1e-3 / dbu)


post_calib_options = ["simulated-cd(dbu) ", " error(nm)"]
class mt_cutline_data:
    flag = False
    def __init__(self, x, dbu):
        if not mt_cutline_data.flag: 
            mt_cutline_data.flag = True
            print("use design cd for test")
        self.pattern_name= x[1]
        self.cutline     = [x[4:6], x[6:8]]
        self.polar       = [-1, 1][int(0 == x[8])]
        self.desigin_cd  = nm_to_dbu(x[9], dbu) 
        self.pitch       = nm_to_dbu(x[10], dbu) 
        self.measured_cd = self.desigin_cd#
        self.measured_cd = nm_to_dbu(x[11], dbu)
        self.weight      = x[16]
        self.check_data(x)
    def check_data(self, x):
        x1,y1 = self.cutline[0]
        x2,y2 = self.cutline[1]
        if (y1 != y2) == (x1 != x2):
            raise Exception(f"cutline check failed {self.cutline}\n{x}")
        # assert((x2 - x1) == self.pitch)

def get_cutline_datas(data, dbu):
    cutline_data = mt_cutline_data
    lines = list()
    # unique_pattern = ["siLEDSP", "LP", "ILP", "BP", "Lin", "Lin_iso", "iLin_iso", "RLin", "sLP", "sBP"]
    ignore_list = []#["siLED90S200P180"]
    # trans_table = str.maketrans('', '', '0123456789')
    for x in data:
        temp = cutline_data(x, dbu)
        # s = temp.pattern_name.translate(trans_table)
        # if s in unique_pattern : continue
        if temp.pattern_name in ignore_list or temp.weight ==0 : continue
        # unique_pattern.append(s)
        lines.append(temp)
    return lines

def clip_layers_by_cutline(gds_path : str, workdir : str,cutlines : np.array, shape : tuple[float, float], layer_id:int, cell_name:str):
    xsize, ysize = shape[0] / 2, shape[1] / 2
    start_points = np.column_stack([
        (cutlines[:, 0] + cutlines[:, 2]) / 2 - xsize, 
        (cutlines[:, 1] + cutlines[:, 3]) / 2 - ysize 
    ])
    start_points = [tuple(map(float, row)) for row in start_points]
    clip_layers(gds_path, workdir, layer_id, start_points, shape, cell_name)


def clip_flow(cutlines_in_um, oas_file, cell_name, layer_id, shape, verbose):
    workdir = subclip_workdir(oas_file)
    args_cache = os.path.join(workdir, "info.bin")
    key_params = (cutlines_in_um.tolist(), oas_file, cell_name, layer_id, shape)
    if os.path.exists(args_cache) and args_from_file(filepath=args_cache) == key_params: 
        print("    subclip alread done")
    else:
        clip_layers_by_cutline(
            oas_file, workdir, cutlines_in_um, shape, layer_id, cell_name
        )
        args_to_file(key_params, filepath=args_cache)
        print("    subclip success")

    if verbose in range(len(cutlines_in_um)):
        def get_midpoints_from_cutline(cutlines : np.array)-> np.array:
            return np.column_stack([
                (cutlines[:, 0] + cutlines[:, 2]) / 2, 
                (cutlines[:, 1] + cutlines[:, 3]) / 2  
            ])
        mid_points_in_um = get_midpoints_from_cutline(cutlines_in_um)
        i = verbose
        print(f"    verbose of {i}.oas")
        draw_oas_with_holes(os.path.join(workdir, f"{i}.oas"), cell_name, layer_id)
        x, y = [mid_points_in_um[i][0]], [mid_points_in_um[i][1]]
        plt.plot(x, y, "y-o")
        plt.plot(cutlines_in_um[i][0:3:2], cutlines_in_um[i][1:4:2], "r-")
        plt.show()
    return workdir

'''
./gauge_io.py \
    /home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_7.ss \
    /home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas \
    JDV_M 300 --shape "8, 8"

./gauge_io.py \
    /home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_7.ss \
    /home/like/model_data/X_File/LG40_poly_File/LG40_PC_CDU_Contour_Mask_L300.oas \
    JDV_M 300 --shape "8, 8" --verbose 3

'''
def main():
    import argparse
    # 创建命令行解析器
    parser = argparse.ArgumentParser(
        description='GDSII文件图层裁剪工具',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # 必需参数
    parser.add_argument(
        'gauge_file',
        type=str,
        help='输入的GAUGE文件路径'
    )
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
    parser.add_argument(
        '--shape',
        type=parse_shape, #str,
        default= "1, 1",
        help='裁剪矩形形状，格式为"width,height"',
        metavar='W,H'
    )
    parser.add_argument(
        "--verbose", 
        type=int,
        default=-1,
        help="cutline 可视化"
    )

    def get_cutline(data : List[Tuple], dbu: float)->list: # N * 4
        arr = np.array([x[4:8] for x in data], np.float64)
        check_pass = True
        x_eq = arr[:, 0] == arr[:, 2]
        y_eq = arr[:, 1] == arr[:, 3]
        check = x_eq != y_eq
        for i in range(len(check)):
            if not check[i]:
                print(f"cutline check failed {arr[i]}")
                check_pass = False
        assert(check_pass)
        return arr * dbu


    args = parser.parse_args()
    gauge_table = read_gauge_file(args.gauge_file)
    cutlines_in_um = get_cutline(gauge_table, get_dbu(args.oas_file))
    print("    load gauge file success")
    return clip_flow(cutlines_in_um, args.oas_file, args.cell_name, args.layer_id, args.shape, args.verbose)

if __name__ == '__main__':
    workdir = main()