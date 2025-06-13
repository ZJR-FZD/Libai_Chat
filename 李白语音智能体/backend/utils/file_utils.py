import os
import shutil
import time
from datetime import datetime
from typing import Optional

def create_dir_if_not_exists(directory: str) -> None:
    """创建目录（如果不存在）"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_unique_filename(prefix: str, extension: str) -> str:
    """生成唯一的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}{timestamp}.{extension}"

def clean_directory(directory: str, age_threshold: int = 3600) -> None:
    """清理目录中超过指定时间的文件"""
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > age_threshold:
                os.remove(file_path)

def save_audio_file(audio_data: bytes, directory: str, prefix: str, extension: str) -> str:
    """保存音频文件并返回文件名"""
    create_dir_if_not_exists(directory)
    filename = generate_unique_filename(prefix, extension)
    file_path = os.path.join(directory, filename)
    
    with open(file_path, "wb") as f:
        f.write(audio_data)
    
    return filename    