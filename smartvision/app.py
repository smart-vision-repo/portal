
# import debugpy
# # 等待调试器连接，10秒超时
# try:
#     debugpy.listen(("localhost", 5678))
#     print("⏳ 等待调试器连接，按Ctrl+C可取消...")
#     debugpy.wait_for_client(timeout=10)
#     print("✅ 调试器已连接!")
#     debugpy.breakpoint()  # 强制设置断点
# except Exception as e:
#     print(f"⚠️ 调试器连接失败: {str(e)}")

import torch
import streamlit as st
import os

# Set page config
torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)]
st.set_page_config(page_title="SmartVision", layout="wide")

# Import components
from ui.components.sidebar import render_sidebar
from ui.components.content import render_content
from common.session import init_session
from common.loader import load_css


# app.py
import streamlit as st
from loguru import logger
import sys

@st.cache_resource # 使用 cache_resource 确保logger配置只运行一次
def get_logger():
    logger.remove() # 清除默认或之前添加的handlers
    logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", level="DEBUG")
    logger.add("app_log_{time:YYYYMMDD}.log", rotation="1 day", retention="3 days", level="INFO")
    logger.info("Logger initialized via st.cache_resource")
    return logger

logger = get_logger()

# load css
load_css(st, "smartvision/ui/static/css/style.css")

# init session values
init_session(st)

# render sidebar
render_sidebar()

# Render main content
render_content()
