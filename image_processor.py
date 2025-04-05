import os
import traceback
from datetime import datetime
from PIL import Image

def process_image(image_path, source_hash, hash_algorithm, min_similarity=0, max_similarity=1, filter_enabled=False):
    """处理单个图像并计算相似度，用于多进程处理"""
    try:
        # 获取文件信息
        file_path = str(image_path)
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        file_type = file_ext[1:].upper()
        
        # 获取文件修改日期
        file_mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(file_mtime)
        
        # 获取图像分辨率和计算哈希
        with Image.open(file_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            width, height = img.size
            resolution = width * height
            resolution_str = f"{width} × {height}"
            
            # 计算图像哈希
            img_hash = hash_algorithm(img)
        
        # 计算相似度
        hash_distance = source_hash - img_hash
        max_distance = len(source_hash.hash) ** 2
        similarity = 1 - (hash_distance / max_distance)
        
        # 应用相似度筛选
        if filter_enabled and (similarity < min_similarity or similarity > max_similarity):
            return None  # 不符合筛选条件
        
        # 返回图像信息
        return {
            'path': file_path,
            'name': file_name,
            'type': file_type,
            'date': file_date,
            'mtime': file_mtime,
            'resolution': resolution,
            'resolution_str': resolution_str,
            'width': width,
            'height': height,
            'similarity': similarity
        }
    except Exception as e:
        print(f"处理图像 {image_path} 时出错: {e}")
        traceback.print_exc()
        return None  # 处理失败返回None

def compute_image_hash(image_path, hash_algorithm):
    """计算图像的哈希值"""
    with Image.open(image_path) as img:
        # 转换为RGB模式（处理RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return hash_algorithm(img)