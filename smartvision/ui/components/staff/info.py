import os
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, LOCAL_DIRS, STAGE, KEY_NAMES
from ui.components.common import on_file_uploaded, append_asistant_message


def render_staff_info_col_info(info_col):

    curr = st.session_state[SESSION_KEYS.STAGE]
    # 右侧信息区域
    with info_col:
        if st.session_state[SESSION_KEYS.COLLECTION_COMPLETE]:
            st.subheader("📋 信息摘要")


        if (curr == STAGE.UPLOADING_VIDEO):
            # 视频上传区域
            st.markdown("### 📹 上传监控视频")
            uploaded_files = st.file_uploader(
                "选择视频文件, 请注意顺序，我们通常从第一个视频开始",
                type=["mp4", "mov", "avi"],
                help="支持MP4, MOV, AVI格式，大小不超过100MB",
                accept_multiple_files=True,
            )

            if uploaded_files is not None and len(uploaded_files) > 0:
                if st.button("确认上传", type="primary", use_container_width=True):
                    on_file_uploaded(uploaded_files, STAGE.SETTING_START_TIME)