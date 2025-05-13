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

        if curr == STAGE.SHOW_PROMPT_SETTING_START_TIME:
            seconds = st.session_state[SESSION_KEYS.START_TIME]
            st.info(f"物品的最后发现时间在视频的{seconds}秒处")
            if st.button("确认"):
                st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_PREPARE_OBJECTS
                st.rerun()

        if curr == STAGE.USER_SETTING_START_TIME:
            if st.button("时间确认"):
                append_asistant_message(f"您选择了从视频第{st.session_state[SESSION_KEYS.START_TIME]}分钟开始查找")
                st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_PREPARE_OBJECTS
                st.rerun()

        if curr == STAGE.CUSTOMER_IDENTIFYING_OBJECTS:
            if st.button("确认选择图片中的物品"):
                identify_objects = st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS]
                identify_object = identify_objects[0]
                object_names = st.session_state[SESSION_KEYS.USER_OBJECT_BOX_INDEX].split("-")
                index = int(object_names[0]) - 1

                customer_indentified_box = identify_object['boxes'][index]
                label = customer_indentified_box['label']
                box = customer_indentified_box['box']
                xyxy = box.xyxy.tolist()
                # xyxy = box.xyxy[0].cpu().numpy()  # Bo
                json = {"label": label, "location": xyxy[0]}
                st.session_state[SESSION_KEYS.USER_OBJECT_BOX] = json
                st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_IDENTIFIED_LOST_OBJECT
                st.rerun()

        if curr == STAGE.START_TIME_COMPLETED:
            pass

        if (curr == STAGE.ALIYUN_UPLOADING_OBJECTS):
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
                    on_file_uploaded(uploaded_files, STAGE.SHOW_PROMPT_SETTING_START_TIME)