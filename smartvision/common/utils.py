import os
import subprocess
import os
import argparse
import platform
import shutil
from typing import Optional
from common.settings import SESSION_KEYS, PROMPT_TEXT, LOCAL_DIRS, STAGE, KEY_NAMES


import torch
import platform

def get_available_device():
    """
    检测并返回可用的最佳计算设备 (MPS, CUDA, 或 CPU).
    优先顺序: MPS (在 macOS上), CUDA, CPU.
    """
    # 检查 Apple Silicon (MPS)
    if platform.system() == "Darwin": # macOS
        if torch.backends.mps.is_available():
            print("MPS (Apple Silicon GPU) 可用。")
            # 还可以检查 MPS 是否真的能工作 (某些旧 macOS 版本或 PyTorch 版本可能有问题)
            try:
                # 创建一个简单的张量并移至 mps 设备以验证
                _ = torch.tensor([1.0, 2.0]).to("mps")
                print("MPS 功能正常。将使用 'mps' 设备。")
                return "mps"
            except Exception as e:
                print(f"MPS 可用但测试失败: {e}。将回退到 CPU。")
                # 如果 MPS 测试失败，通常回退到 CPU，因为 CUDA 在 Mac 上不被原生支持
        else:
            print("MPS 不可用。")
    
    # 检查 NVIDIA CUDA
    if torch.cuda.is_available():
        print("CUDA (NVIDIA GPU) 可用。")
        cuda_device_count = torch.cuda.device_count()
        print(f"找到 {cuda_device_count} 个 CUDA 设备。")
        if cuda_device_count > 0:
            # 获取第一个 CUDA 设备的名称
            cuda_device_name = torch.cuda.get_device_name(0)
            print(f"将使用 CUDA 设备 0: {cuda_device_name}")
            return "cuda" # 或者 "cuda:0"
    else:
        print("CUDA 不可用。")
        
    print("MPS 和 CUDA 均不可用。将使用 'cpu' 设备。")
    return "cpu"


def get_str_time(time):
    values = time.split("-")
    str = ""
    hours = False
    if int(values[0]) > 0:
        hours = True
        str += f"{values[0]}小时"
    
    if int(values[1]) > 0:
        str += f"{values[1]}分"

    if int(values[2]) > 0:
        str += f"{values[2]}秒"
    return str

def scroll_to_bottom_markdown(st):
    """使用 Markdown 注入滚动到底部的 JavaScript"""
    js = """
    <script>
        function scroll() {
            try {
                 window.parent.document.body.scrollTop = window.parent.document.body.scrollHeight;
            } catch (e) {
                 // Fallback if parent access fails
                 window.scrollTo(0, document.body.scrollHeight);
            }
        }
        setTimeout(scroll, 150); // Small delay to ensure content renders
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


def get_resource_dir(st):
    video_path = (
        f"{LOCAL_DIRS.TMP_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}/videos"
    )
    image_path = (
        f"{LOCAL_DIRS.TMP_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}/results"
    )
    return video_path, image_path

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