import os
import subprocess
import os
import argparse
import platform
import shutil
from typing import Optional


def check_gpu_availability() -> tuple[bool, Optional[str]]:
    """检查系统是否有可用的GPU，并返回适合的FFmpeg硬件加速选项"""
    # 检查NVIDIA GPU
    try:
        # 检查nvidia-smi是否可用
        nvidia_output = subprocess.check_output(
            ["nvidia-smi"], stderr=subprocess.STDOUT
        )
        print("NVIDIA GPU detected.")
        return True, "cuda"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 检查AMD GPU (Linux)
    if platform.system() == "Linux":
        try:
            amd_output = subprocess.check_output(["lspci"], stderr=subprocess.STDOUT)
            if b"AMD" in amd_output and (
                b"VGA" in amd_output or b"Display" in amd_output
            ):
                print("AMD GPU detected on Linux.")
                return True, "amf"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # 检查Intel GPU
    if platform.system() == "Windows":
        try:
            dxdiag_output = subprocess.check_output(
                ["dxdiag", "/t"], stderr=subprocess.STDOUT
            )
            if b"Intel" in dxdiag_output and (
                b"Graphics" in dxdiag_output or b"Display" in dxdiag_output
            ):
                print("Intel GPU detected on Windows.")
                return True, "qsv"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    elif platform.system() == "Linux":
        try:
            lspci_output = subprocess.check_output(["lspci"], stderr=subprocess.STDOUT)
            if b"Intel" in lspci_output and (
                b"VGA" in lspci_output or b"Display" in lspci_output
            ):
                print("Intel GPU detected on Linux.")
                return True, "qsv"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # macOS 的 Apple Silicon 或 Intel 集成显卡
    if platform.system() == "Darwin":
        try:
            sysctl_output = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], stderr=subprocess.STDOUT
            )
            if b"Apple" in sysctl_output:
                print("Apple Silicon detected.")
                return True, "videotoolbox"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    print("No compatible GPU detected or drivers not installed. Using CPU.")
    return False, None

def list_directories(path):
    all_items = os.listdir(path)
    # Filter out only the directories
    return [item for item in all_items if os.path.isdir(os.path.join(".", item))]

def frame_index_to_time(frame_index, fps):
    seconds = frame_index / fps
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60  
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def list_video_files(path):
    return [
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and f.endswith((".mp4", ".avi", ".mov"))  # Check for video files
    ]


def list_image_files(path):
    """
    获取指定路径下的所有图片文件。

    Args:
        path (str): 图片文件所在的目录路径。

    Returns:
        list: 包含图片文件名的列表。
    """
    return [
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
        and f.endswith((".jpg", ".jpeg", ".png"))  # Check for video files
    ]


if __name__ == '__main__':
    print(list_directories("."))