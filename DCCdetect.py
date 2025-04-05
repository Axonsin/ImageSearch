# unity_utils.py（独立的检测模块）
import psutil
from pathlib import Path
import sys
import os
import subprocess
from qtpy import QtWidgets, QtCore, QtGui


def get_unity_project_paths(): 
    system = sys.platform
    project_paths = []  # 使用列表存储多个项目
    error = 0
    
    if system == "win32":
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'Unity.exe':
                cmdline = proc.info['cmdline']
                if cmdline:
                    for i, arg in enumerate(cmdline):
                        if arg.lower() == '-projectpath' and i + 1 < len(cmdline):
                            project_path = cmdline[i + 1]
                            if project_path not in project_paths:  
                                project_paths.append(project_path)
    else:
        error = 1
        return [], error

    # 调试信息保留
    print(f"系统平台: {system}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'unity' in proc.info['name'].lower():
            print(f"找到Unity相关进程: {proc.info['name']} (PID: {proc.info['pid']})")
            print(f"命令行参数: {proc.info['cmdline']}")
            
    return project_paths, error

    # 调试信息保留
    print(f"系统平台: {system}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'unity' in proc.info['name'].lower():
            print(f"找到Unity相关进程: {proc.info['name']} (PID: {proc.info['pid']})")
            print(f"命令行参数: {proc.info['cmdline']}")
            
    return project_paths, error

    # 在get_unity_project_path函数中添加调试信息
    print(f"系统平台: {system}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'unity' in proc.info['name'].lower():
            print(f"找到Unity相关进程: {proc.info['name']} (PID: {proc.info['pid']})")
            print(f"命令行参数: {proc.info['cmdline']}")
    return project_path, error


def get_blender_project_paths():
    """检测当前运行的Blender进程并获取项目路径"""
    system = sys.platform
    project_paths = []  # 使用列表存储多个项目
    error = 0
    
    if system in ["win32", "darwin", "linux"]:  # 支持Windows、macOS和Linux
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # 检查进程名是否与Blender相关
            process_name = proc.info['name'].lower()
            if ('blender' in process_name):
                cmdline = proc.info['cmdline']
                if cmdline:
                    # 搜索命令行中的.blend文件
                    for arg in cmdline:
                        if arg.lower().endswith('.blend'):
                            # 获取.blend文件所在文件夹
                            blend_file = arg
                            project_path = str(Path(arg).parent)
                            
                            # 项目信息字典，包含文件夹路径和文件名
                            project_info = {
                                'folder': project_path,
                                'file': str(Path(arg).name),
                                'full_path': blend_file
                            }
                            
                            # 检查是否已经添加过这个项目
                            if project_path not in [p['folder'] for p in project_paths]:
                                project_paths.append(project_info)
    else:
        error = 1
        return [], error

    # 调试信息
    print(f"系统平台: {system}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'blender' in proc.info['name'].lower():
            print(f"找到Blender相关进程: {proc.info['name']} (PID: {proc.info['pid']})")
            print(f"命令行参数: {proc.info['cmdline']}")
            
    return project_paths, error

def open_blender_project(project_path):
    """打开Blender项目文件夹"""
    return open_project_folder(project_path)





def open_project_folder(path):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(['open', path])
    else:
        return "无法打开文件夹，请手动操作。"

def show_message_box(parent, title, message, info=True):
    if info:
        QtWidgets.QMessageBox.information(parent, title, message)
    else:
        QtWidgets.QMessageBox.warning(parent, title, message)