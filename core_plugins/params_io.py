#!/usr/bin/env python3
import tempfile
import pickle
from typing import Any, Tuple
import os

def serialize(obj) -> bytes:
    """
    将任意Python对象序列化为字节流
    :param obj: 任意Python对象（支持基本类型、列表、字典、自定义类等）
    :return: 序列化后的字节流
    """
    return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

def deserialize(serialized_data: bytes):
    """
    将字节流反序列化为原始Python对象
    :param serialized_data: 序列化后的字节流
    :return: 原始Python对象
    """
    return pickle.loads(serialized_data)

def args_to_file(*args: Any, filepath: str) -> str:
    """
    将任意数量的参数序列化并保存到文件
    
    Args:
        *args: 要序列化的任意参数
        filepath: 文件名
    
    Returns:
        保存的文件路径
    """
    with open(filepath, 'wb') as f:
        f.write(pickle.dumps(args))
    
    return filepath
def args_from_file(filepath: str) -> Tuple[Any, ...]:
    """
    从文件中加载并反序列化参数
    
    Args:
        filepath: 之前通过 args_to_file 保存的文件路径
        
    Returns:
        包含原始参数的元组
        
    Raises:
        FileNotFoundError: 如果文件不存在
        pickle.UnpicklingError: 如果文件内容不是有效的序列化数据
    """
    # 读取的结果等于 (args_to_file,)
    with open(filepath, 'rb') as f:
        return pickle.load(f)[0] 

def example():
    # 示例用法
    data = {"name": "Alice", "age": 30, "tags": ["python", "coding"]}
    serialized = serialize(data)
    restored_data = deserialize(serialized)
    print(restored_data)  # 输出: {'name': 'Alice', 'age': 30, 'tags': ['python', 'coding']}