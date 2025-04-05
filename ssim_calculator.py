# ssim_calculator.py
import numpy as np
from PIL import Image

def calculate_ssim(img1_path, img2_path, window_size=11, k1=0.01, k2=0.03, L=255):
    """
    SSIM计算
        img1_path, img2_path: 两个图像的路径
        window_size: 计算结构相似性时的窗口大小
        k1, k2: 稳定常数
        L: 像素值的动态范围
    
    返回值:
        ssim_value: 0到1之间的相似度值，1表示完全相同
    """
    # 加载图像并转换为灰度图
    img1 = Image.open(img1_path).convert('L')
    img2 = Image.open(img2_path).convert('L')
    
    # 将图像调整为相同尺寸以进行比较
    # 使用较小图像的尺寸作为目标尺寸
    width = min(img1.width, img2.width)
    height = min(img1.height, img2.height)
    img1 = img1.resize((width, height), Image.LANCZOS)
    img2 = img2.resize((width, height), Image.LANCZOS)
    
    # 转换为numpy数组以进行数学运算
    img1 = np.array(img1, dtype=np.float64)
    img2 = np.array(img2, dtype=np.float64)
    
    # 计算均值
    mu1 = np.mean(img1)
    mu2 = np.mean(img2)
    
    # 计算方差和协方差
    sigma1_sq = np.var(img1)
    sigma2_sq = np.var(img2)
    sigma12 = np.mean((img1 - mu1) * (img2 - mu2))
    
    # 计算稳定常数
    C1 = (k1 * L) ** 2
    C2 = (k2 * L) ** 2
    C3 = C2 / 2
    
    # 计算亮度、对比度和结构对比
    l = (2 * mu1 * mu2 + C1) / (mu1**2 + mu2**2 + C1)  # 亮度
    c = (2 * np.sqrt(sigma1_sq) * np.sqrt(sigma2_sq) + C2) / (sigma1_sq + sigma2_sq + C2)  # 对比度
    s = (sigma12 + C3) / (np.sqrt(sigma1_sq) * np.sqrt(sigma2_sq) + C3)  # 结构
    
    # 计算SSIM
    ssim_value = l * c * s
    
    return ssim_value

def compare_images_ssim(source_path, target_path):
    """
    计算两个图像的SSIM相似度，用于多进程调用
    
    参数:
        source_path: 源图像路径
        target_path: 目标图像路径
    
    返回值:
        0到1之间的相似度值
    """
    try:
        return calculate_ssim(source_path, target_path)
    except Exception as e:
        print(f"SSIM计算错误: {e}")
        return 0.0  # 出错时返回0相似度