# unity_utils.py（独立的检测模块）
import psutil
from pathlib import Path
import sys
import os
import subprocess
from qtpy import QtWidgets, QtCore, QtGui


def get_unity_project_path():
    system = sys.platform
    project_path = None
    error = 0
    if system == "win32":
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'Unity.exe':
                cmdline = proc.info['cmdline']
                if cmdline:
                    for i, arg in enumerate(cmdline):
                        if arg.lower() == '-projectpath' and i + 1 < len(cmdline):
                            project_path = cmdline[i + 1]
                            break
    elif system == "darwin":
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'Unity':
                cmdline = proc.info['cmdline']
                if cmdline:
                    for i, arg in enumerate(cmdline):
                        if arg == '-projectPath' and i + 1 < len(cmdline):
                            project_path = cmdline[i + 1]
                            break
    else:
        error = 1
        return None, error

    # 在get_unity_project_path函数中添加调试信息
    print(f"系统平台: {system}")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'unity' in proc.info['name'].lower():
            print(f"找到Unity相关进程: {proc.info['name']} (PID: {proc.info['pid']})")
            print(f"命令行参数: {proc.info['cmdline']}")
    return project_path, error


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