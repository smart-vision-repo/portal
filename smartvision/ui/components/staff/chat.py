import os
import logging
import sys
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, STAGE, KEY_NAMES
from common.loader import show_md_content
from common.utils import list_image_files, get_resource_dir

from ai.common.yolo import yolo_find_objects_by_images, detect_object_loss_time
from ai.common.cv import cv_extract_frames, cv_clip_video

from ui.components.staff.info import render_staff_info_col_info
from ui.components.common import show_assistant_animation_message

from ai.pet.llm import  initialize_chat

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()


def render_staff_col_chat(chat_col, info_col):
    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.COMPLETED_NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()

    # 创建两列布局
    # chat_col, info_col = st.columns([3, 2])

    # 左侧聊天区域
    with chat_col:
        if not st.session_state[SESSION_KEYS.INITIALIZED]:
            welcome_message = "您好！我是失物寻找，请您上传监控视频."
            initialize_chat(st, welcome_message)
            st.session_state[SESSION_KEYS.STAGE] = STAGE.ALIYUN_UPLOADING_OBJECTS
        # 显示对话历史
        chat_container = st.container()

        with chat_container:
            for message in st.session_state[SESSION_KEYS.MESSAGES]:
                if message["role"] != "system":  # 不显示系统消息
                    with st.chat_message(message["role"]):
                        st.markdown(
                            message["content"],
                            unsafe_allow_html=True,
                        )

        # 如果正在处理，显示加载动画
        if st.session_state[SESSION_KEYS.PROCESSING]:
            show_assistant_animation_message(PROMPT_TEXT.AI_THINKING)

        if curr <= STAGE.SHOW_PROMPT_UPLOADING_VIDEO:
            st.session_state[SESSION_KEYS.STAGE] = STAGE.ALIYUN_UPLOADING_OBJECTS
            show_assistant_animation_message(PROMPT_TEXT.STAFF_UPLOADING_VIDEO)
            st.rerun()

        if curr == STAGE.SHOW_PROMPT_SETTING_START_TIME:
            show_prompt_setting_start_time()

        if curr == STAGE.USER_SETTING_START_TIME:
            set_start_time()

        # 准备图片，用于用户指认物品.
        if curr == STAGE.CUSTOMER_PREPARE_OBJECTS:
            prepare_images()

        # 显示图片
        if curr == STAGE.CUSTOMER_IDENTIFYING_OBJECTS:
            identifying_objects()

        # 用户指认物品完成, 开始准备查找
        if curr == STAGE.CUSTOMER_IDENTIFIED_LOST_OBJECT:
            show_searching_prompt()

        # clip object lost scenario video
        if curr == STAGE.SEARCHING_COMPLETED:
            show_assistant_animation_message("失物的丢失时间已找到, 正在剪切视频")
            clip_video()


    render_staff_info_col_info(info_col)



def clip_video():
    video_dir, result_dir = get_resource_dir(st)
    clip_time = st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME]
    lost_time = clip_time["lost_time"]
    if cv_clip_video(
        clip_time["file_name"], lost_time - 10.0, lost_time + 10.0, result_dir
    ):
        st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_OBJECT_IDENTIFIED
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS
    st.rerun()


def show_uploading_objects_prompt():
    with st.chat_message("assistant"):
        show_md_content(
            st,
            KEY_NAMES.FILE_LOADING_ANIMATION,
            "正在上传资料，供确认",
        )
    st.session_state[STAGE] = STAGE.ALIYUN_UPLOADING_OBJECTS
    st.rerun()


def on_searching_callback():
    pass


def show_searching_prompt():
    video_path, result_dire = get_resource_dir(st)
    with st.chat_message("assistant"):
        show_md_content(
            st,
            KEY_NAMES.FILE_LOADING_ANIMATION,
            PROMPT_TEXT.IDENTIFING_OBJECT,
        )
    box = st.session_state[SESSION_KEYS.USER_OBJECT_BOX]
    result = detect_object_loss_time(
        video_path=video_path,
        target_label=box["label"],
        target_box=box["location"],
        tolerance_seconds=5.0,
    )
    if result:
        st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME] = result
        st.session_state[SESSION_KEYS.STAGE] = STAGE.SEARCHING_COMPLETED
        st.rerun()
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS


def show_preparing_prompt():
    show_assistant_animation_message("正在准备图片，供您确认物品")


def prepare_images():
    show_assistant_animation_message("正在准备图片...")
    video_path, result_dir = get_resource_dir(st)
    start_time = st.session_state[SESSION_KEYS.START_TIME]
    results = cv_extract_frames(
        # 从指定时间开始取一帧图片，供客户确认物品的位置
        on_extracting,
        None,
        video_path,
        result_dir,
        start_time,
        1,
        1,
        1,
    )
    if results and len(results) > 0:
        files = list_image_files(result_dir)
        if len(files) == 0:
            st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS
            st.rerun()
        identified_objects = yolo_find_objects_by_images(
            yolo_identifying_callback, None, result_dir, None, 0.2, True
        )
        st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = identified_objects
        st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_IDENTIFYING_OBJECTS
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS
    st.rerun()


def identifying_objects():
    identify_objects = st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS]

    if len(identify_objects) == 0:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS
        st.rerun()

    show_assistant_animation_message("请识别图片中的物件，点击可放大...")
    video_dir, result_dir = get_resource_dir(st)
    files = list_image_files(result_dir)
    with st.chat_message("assistant"):
        col_index = 0
        image_cols = st.columns(3)
        for file_name in files:
            with image_cols[col_index]:
                st.image(
                    os.path.join(result_dir, file_name),
                    caption="请在图中确认你的物品",
                    use_container_width=True,
                )
            col_index += 1

    options = []
    obj = identify_objects[0]
    for box in obj["boxes"]:
        options.append(f"{box['box_index']}-{box['label']}")

    with st.chat_message("assistant"):
        st.radio(
            label="请选择您的物件",
            options=options,
            horizontal=True,
            key=SESSION_KEYS.USER_OBJECT_BOX_INDEX,
        )


def yolo_identifying_callback(placeholder, file_name):
    pass


def on_extracting(placeholder, index, total):
    pass


def show_prompt_setting_start_time():
    st.session_state[SESSION_KEYS.STAGE] = STAGE.USER_SETTING_START_TIME
    st.rerun()


def set_start_time():
    videos = st.session_state[SESSION_KEYS.VIDEOS]
    if not videos or len(videos) == 0:
        st.error("没有找到视频信息，请先上传视频")
        return

    video = videos[0]  # 取第一个视频
    with st.chat_message("assistant"):
        st.slider(
            label=PROMPT_TEXT.STAFF_UPLOADING_VIDEO,
            min_value=0,
            max_value=int(video["duration"]),
            key=SESSION_KEYS.START_TIME,
        )
