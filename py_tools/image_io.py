from PIL import Image
import numpy as np
import argparse
import os
from typing import Optional, Union
import io

class RobustImageIO:
    """
    增强版图片读写接口，支持：
    1. 使用 Pillow 读写常规图片格式
    2. 当 Pillow 失败时自动回退到二进制格式 (.bin)
    3. 支持读取二进制格式保存的图像
    """
    
    @staticmethod
    def read_image(file_path: str) -> np.ndarray:
        """
        读取图片文件或二进制文件到 numpy 数组
        
        参数:
            file_path: 图片文件路径 (.jpg, .png, .bin 等)
            
        返回:
            np.ndarray: 图像数据，形状为 (H,W) 或 (H,W,C)
            
        异常:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不受支持或已损坏
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 如果是 .bin 文件，使用二进制方式读取
        if file_path.lower().endswith('.bin'):
            try:
                with open(file_path, 'rb') as f:
                    # 二进制文件的前24字节是元数据 (3个int64: ndim, shape[0], shape[1])
                    metadata = np.frombuffer(f.read(24), dtype=np.int64)
                    ndim, height, width = metadata[0], metadata[1], metadata[2]
                    
                    # 如果是3D数组，读取第4个维度 (channels)
                    if ndim == 3:
                        channels = np.frombuffer(f.read(8), dtype=np.int64)[0]
                        shape = (height, width, channels)
                    else:
                        shape = (height, width)
                    
                    # 读取剩余数据 (图像内容)
                    array_data = np.frombuffer(f.read(), dtype=np.uint8)
                    return array_data.reshape(shape)
            except Exception as e:
                raise ValueError(f"读取二进制文件失败: {str(e)}")
        
        # 否则尝试用 Pillow 读取
        try:
            with Image.open(file_path) as img:
                # 转换模式确保一致性
                if img.mode == 'P':
                    img = img.convert('RGB')
                elif img.mode == 'PA':
                    img = img.convert('RGBA')
                elif img.mode == 'L':
                    pass
                elif img.mode == 'LA':
                    img = img.convert('RGBA')
                elif img.mode == 'RGB':
                    pass
                elif img.mode == 'RGBA':
                    pass
                elif img.mode == 'CMYK':
                    img = img.convert('RGB')
                else:
                    raise ValueError(f"不支持的图像模式: {img.mode}")
                
                img_array = np.array(img)
                
                if len(img_array.shape) == 2:
                    img_array = np.expand_dims(img_array, axis=-1)
                
                return img_array
        except Exception as e:
            # 如果 Pillow 读取失败，尝试查找同名的 .bin 文件
            bin_path = os.path.splitext(file_path)[0] + '.bin'
            if os.path.exists(bin_path):
                return RobustImageIO.read_image(bin_path)
            raise ValueError(f"无法读取图片文件 {file_path}: {str(e)}")
    
    @staticmethod
    def write_image(file_path: str, image_array: np.ndarray, 
                   quality: Optional[int] = None, **kwargs) -> bool:
        """
        将 numpy 数组写入图片文件，失败时自动保存为二进制格式
        
        参数:
            file_path: 输出文件路径
            image_array: numpy 数组，形状为 (H,W) 或 (H,W,C)
            quality: 对于有损格式的质量 (1-100)
            **kwargs: Pillow 保存参数
            
        返回:
            bool: 是否成功保存 (True=成功保存为图片, False=保存为二进制)
            
        异常:
            ValueError: 如果图像数据无效
        """
        if not isinstance(image_array, np.ndarray):
            raise ValueError("输入必须是 numpy 数组")
        
        # 检查数组形状
        if len(image_array.shape) not in (2, 3):
            raise ValueError("图像数组必须是 2D(灰度) 或 3D(彩色)")
        
        # 处理数据类型
        if image_array.dtype != np.uint8:
            if np.issubdtype(image_array.dtype, np.floating):
                image_array = (np.clip(image_array, 0, 1) * 255).astype(np.uint8)
            else:
                image_array = image_array.astype(np.uint8)
        
        # 首先尝试用 Pillow 保存
        try:
            # 确定图像模式
            if len(image_array.shape) == 2 or image_array.shape[2] == 1:
                mode = 'L'
                if len(image_array.shape) == 3:
                    image_array = image_array[:, :, 0]
            elif image_array.shape[2] == 3:
                mode = 'RGB'
            elif image_array.shape[2] == 4:
                mode = 'RGBA'
            else:
                raise ValueError(f"不支持的通道数: {image_array.shape[2]}")
            
            img = Image.fromarray(image_array, mode)
            
            # 准备保存参数
            save_kwargs = kwargs.copy()
            if quality is not None:
                save_kwargs['quality'] = quality
            
            # 特殊格式处理
            ext = file_path[file_path.rfind('.')+1:].lower()
            if ext in ('jpg', 'jpeg'):
                save_kwargs.setdefault('quality', 95)
                save_kwargs.setdefault('subsampling', 0)
            elif ext == 'webp':
                save_kwargs.setdefault('quality', 80)
            elif ext == 'png':
                save_kwargs.setdefault('compress_level', 6)
            
            img.save(file_path, **save_kwargs)
            return True
        except Exception as e:
            print(f"警告: 使用 Pillow 保存失败，将回退到二进制格式: {str(e)}")
            
            # 保存为二进制格式
            bin_path = os.path.splitext(file_path)[0] + '.bin'
            return RobustImageIO._save_as_bin(bin_path, image_array)
    
    @staticmethod
    def _save_as_bin(file_path: str, image_array: np.ndarray) -> bool:
        """
        内部方法: 将 numpy 数组保存为二进制文件
        
        参数:
            file_path: 输出 .bin 文件路径
            image_array: 要保存的 numpy 数组
            
        返回:
            bool: 是否成功保存
        """
        try:
            with open(file_path, 'wb') as f:
                # 写入元数据 (ndim, height, width[, channels])
                metadata = np.array([image_array.ndim, image_array.shape[0], image_array.shape[1]], dtype=np.int64)
                f.write(metadata.tobytes())
                
                # 如果是3D数组，写入通道数
                if image_array.ndim == 3:
                    channels = np.array([image_array.shape[2]], dtype=np.int64)
                    f.write(channels.tobytes())
                
                # 写入图像数据
                f.write(image_array.tobytes())
            return False  # 表示保存为二进制格式
        except Exception as e:
            raise ValueError(f"保存二进制文件失败: {str(e)}")
    
    @staticmethod
    def get_supported_formats() -> dict:
        """
        获取支持的图片格式
        
        返回:
            dict: {'read': [可读格式], 'write': [可写格式], 'binary': bool}
                 其中 binary=True 表示支持二进制回退
        """
        return {
            'read': list(Image.OPEN.keys()) + ['bin'],
            'write': list(Image.SAVE.keys()) + ['bin'],
            'binary_fallback': True
        }

# 使用示例
def test():
    # 查看支持的格式
    print("支持的格式:", RobustImageIO.get_supported_formats())
    
    try:
        # 创建一个测试图像
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[:, :, 0] = 255  # 红色
        
        # 正常保存为 JPEG
        print("\n测试正常保存:")
        result = RobustImageIO.write_image("test_output.jpg", test_img)
        print(f"保存结果: {'图片格式' if result else '二进制格式'}")
        
        # 读取测试
        loaded_img = RobustImageIO.read_image("test_output.jpg")
        print(f"读取成功，形状: {loaded_img.shape}")
        
        # 测试二进制回退 - 故意使用无效扩展名
        print("\n测试二进制回退:")
        result = RobustImageIO.write_image("test_output.invalid", test_img)
        print(f"保存结果: {'图片格式' if result else '二进制格式'}")
        
        # 读取二进制文件
        loaded_bin = RobustImageIO.read_image("test_output.bin")
        print(f"从二进制文件读取成功，形状: {loaded_bin.shape}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图片格式转换工具")
    parser.add_argument("input_path", type=str, help="输入文件路径")
    parser.add_argument("output_path", type=str, help="输出文件路径")
    args = parser.parse_args()

    try:
        # 读取输入文件
        image_array = RobustImageIO.read_image(args.input_path)

        # 写入输出文件
        RobustImageIO.write_image(args.output_path, image_array)

        print(f"成功将 {args.input_path} 转换为 {args.output_path}")

    except Exception as e:
        print(f"转换失败: {str(e)}")