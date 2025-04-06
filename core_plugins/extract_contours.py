#!/usr/bin/env python3
import cv2
import numpy as np

def extract_contours(gray_image, threshold_value):
    # 先检查输入是否是合法的二维数组
    if not isinstance(gray_image, np.ndarray) or len(gray_image.shape) != 2:
        raise ValueError("输入必须是二维NumPy数组")
    lb, ub = gray_image.min(), gray_image.max()
    normalized = (gray_image - lb) / (ub- lb)
    gray_image = (normalized * 255).astype(np.uint8)
    threshold_value = int(255 * (threshold_value -lb)/ (ub-lb))
    print(f"threshold_value = {threshold_value}")
    # 后续处理与之前相同
    _, binary = cv2.threshold(gray_image, threshold_value, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    output_image = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(output_image, contours, -1, (0,255,0), 1)
    
    return contours, output_image

def show_contuor(im, th):
    contours, result = extract_contours(im, threshold_value=th)
    # 显示结果
    cv2.imshow('Contours', result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
if __name__ == "__main__":
    show_contuor(np.random.randint(0, 256, size=(100, 100), dtype=np.uint8))