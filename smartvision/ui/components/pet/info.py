import os
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, STAGE, KEY_NAMES
from ui.components.common import on_file_uploaded


def render_pet_info_col_info(info_col):

    curr = st.session_state[SESSION_KEYS.STAGE]
    # 右侧信息区域
    with info_col:
        if st.session_state[SESSION_KEYS.COLLECTION_COMPLETE]:
            st.subheader("📋 宠物信息摘要")
            st.info(generate_summary())

        # 执行查找
        if curr == STAGE.SHOW_PROPMPT_SEARCHING:
            if st.button("开始查找", type="primary", use_container_width=True):
                ready_for_extracting_frames()

        if (
            not st.session_state[SESSION_KEYS.VIDEO_UPLOADED]
            and st.session_state[SESSION_KEYS.COLLECTION_COMPLETE]
        ):
            # 视频上传区域
            st.markdown("### 📹 上传宠物视频")
            st.markdown("请上传您宠物的视频，这将帮助我们更快地找到它")

            uploaded_files = st.file_uploader(
                "选择视频文件",
                type=["mp4", "mov", "avi"],
                help="支持MP4, MOV, AVI格式，大小不超过100MB",
                accept_multiple_files=True,
            )

            if uploaded_files is not None and len(uploaded_files) > 0:
                if st.button("确认上传", type="primary", use_container_width=True):
                    on_file_uploaded(uploaded_files, STAGE.CUSTOMER_VIDEO_CLIPPED)
        # 显示结果
        if curr == STAGE.ALIYUN_OBJECTS_UPLOADED:
            show_identified_images()


def show_identified_images():
    filterd_objects = st.session_state[SESSION_KEYS.FILTERED_OBJECTS]
    if len(filterd_objects) == 0:
        return
    items = []
    index = 0
    for obj in filterd_objects:
        index += 1
        file_name = obj["file_name"]
        img = f"{KEY_NAMES.ALIYUN_OSS}/identified/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}/{file_name.split('/')[-1]}"
        items.append(dict(img=img, text="", title=f"{index}", link=img))
    st.subheader(f"🔥 已识别的宠物图片({index})")
    carousel(
        items=items,
        width=1.0,
        key="identified_objects_carousel",
        container_height=200,
    )


def generate_summary():
    """生成宠物信息总结"""
    pet_info = st.session_state[SESSION_KEYS.PET_INFO]
    summary = f"""
    已收集的宠物信息摘要：
    - 宠物类型：{pet_info['pet_type']}
    - 品种：{pet_info['breed']}
    - 颜色：{pet_info['color']}
    - 最后见到时间：{pet_info['last_seen_time']}
    """
    if pet_info["extra_info"]:
        summary += f"- 额外信息：{pet_info['extra_info']}\n"
    return summary


def ready_for_extracting_frames():
    st.session_state[SESSION_KEYS.STAGE] = STAGE.EXTRACTIING_IMAGES
    st.rerun()