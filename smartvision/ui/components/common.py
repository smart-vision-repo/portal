import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, LOCAL_DIRS, STAGE, KEY_NAMES
from common.loader import show_md_content
from ai.common.cv import cv_video_info
import os


def append_asistant_message(message):
    st.session_state[SESSION_KEYS.MESSAGES].append(
        {"role": "assistant", "content": message}
    )

def append_user_message(message):
    st.session_state[SESSION_KEYS.MESSAGES].append({"role": "user", "content": message})


def show_assistant_animation_message(message):
    with st.chat_message("assistant"):
        show_md_content(
            st,
            KEY_NAMES.FILE_LOADING_ANIMATION,
            message,
        )


def on_file_uploaded(uploaded_files, next_stage):
    """处理视频上传"""
    if uploaded_files:
        video_dir = (
            f"{LOCAL_DIRS.VIDEO_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}"
        )
        os.makedirs(video_dir, exist_ok=True)  # 确保目录存在
        index = 1
        for uploaded_file in uploaded_files:
            file_path = os.path.join(video_dir, f"{index}-{uploaded_file.name}")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"文件 '{uploaded_file.name}' 已保存至 {video_dir}")
            index += 1
        st.session_state[SESSION_KEYS.PROCESSING] = False
        st.session_state[SESSION_KEYS.VIDEO_UPLOADED] = True
        st.session_state[SESSION_KEYS.UPLOADED_FILES] = uploaded_files
        
        # 获取视频时长信息，用于计费.
        videos = cv_video_info(video_dir)
        st.session_state[SESSION_KEYS.VIDEOS] = videos
        total = 0
        for video in videos:
            total += video["duration"]
        append_asistant_message(f"视频上传成功, 共{len(uploaded_files)}个， 总时长约{total}秒")
        st.session_state[SESSION_KEYS.STAGE] = next_stage
        st.rerun()