import os
import sys
import subprocess
import psutil
from pathlib import Path

def get_unity_project_path():
    """
    检测当前运行的 Unity 项目路径。
    支持 Windows 和 macOS 系统。
    """
    system = sys.platform
    project_path = None

    if system == "win32":
        # Windows: 查找 Unity.exe 进程的命令行参数
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'Unity.exe':
                cmdline = proc.info['cmdline']
                if cmdline:
                    # 寻找 -projectPath 参数后的路径
                    for i, arg in enumerate(cmdline):
                        if arg == '-projectPath' and i + 1 < len(cmdline):
                            project_path = cmdline[i + 1]
                            break
    elif system == "darwin":
        # macOS: 查找 Unity 进程的命令行参数
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'Unity':
                cmdline = proc.info['cmdline']
                if cmdline:
                    for i, arg in enumerate(cmdline):
                        if arg == '-projectPath' and i + 1 < len(cmdline):
                            project_path = cmdline[i + 1]
                            break
    else:
        print("当前操作系统不支持该脚本。")
        return None

    return project_path

def open_project_folder(path):
    """
    根据操作系统打开文件夹。
    """
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(['open', path])
    else:
        print("无法打开文件夹，请手动操作。")

def main():
    project_path = get_unity_project_path()

    if not project_path:
        print("未检测到正在运行的 Unity 项目。")
        return

    # 确保路径存在
    if not Path(project_path).exists():
        print("检测到项目路径，但路径不存在。")
        return

    # 询问用户是否打开
    print(f"检测到当前 Unity 项目路径：{project_path}")
    choice = input("是否打开该项目文件夹？(Y/N): ").strip().lower()
    if choice == 'y':
        open_project_folder(project_path)
        print("正在打开项目文件夹...")
    else:
        print("操作已取消。")

if __name__ == "__main__":
    main()