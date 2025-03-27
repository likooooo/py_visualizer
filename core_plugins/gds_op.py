#!/usr/bin/env python3
import gdspy
import numpy as np

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

if __name__ == "__main__":
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