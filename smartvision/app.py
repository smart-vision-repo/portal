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

# load css
load_css(st, "ui/static/css/style.css")


# file = "/var/tmp/smart-vision/image/57f0aba9-3da7-4790-baea-863a21641c9c/identified/1-mobile-phone.mp4"
# video_file = open(file, "rb")
# video_bytes = video_file.read()
# st.video(video_bytes)

# init session values
init_session(st)

# render sidebar
render_sidebar()

# Render main content
render_content()
