import os
import logging
import sys
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, STAGE, KEY_NAMES
from common.loader import show_md_content
from common.utils import list_image_files, get_resource_dir, scroll_to_bottom_markdown

from ai.common.yolo import yolo_find_objects_by_images, detect_object_loss_time
from ai.common.cv import cv_extract_frames, cv_clip_video

from ui.components.staff.info import render_staff_info_col_info
from ui.components.common import show_assistant_animation_message, show_assistant_messages, append_asistant_message

from ai.pet.llm import  initialize_chat

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()


def render_staff_col_chat(chat_col, info_col):
    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()


    # 左侧聊天区域
    with chat_col:
        if not st.session_state[SESSION_KEYS.INITIALIZED]:
            welcome_message = "您好！我是失物寻找助手，请您上传监控视频."
            initialize_chat(st, welcome_message)
            st.session_state[SESSION_KEYS.STAGE] = STAGE.UPLOADING_VIDEO
        # 显示对话历史
        chat_container = st.container()
        show_assistant_messages(chat_container)

        if curr < STAGE.UPLOADING_VIDEO:
            st.session_state[SESSION_KEYS.STAGE] = STAGE.UPLOADING_VIDEO
            show_assistant_animation_message(PROMPT_TEXT.STAFF_UPLOADING_VIDEO)
            st.rerun()

        if curr == STAGE.SETTING_START_TIME:
            set_start_time()

        # 准备图片，用于用户指认物品.
        if curr == STAGE.PREPARE_IMAGES:
            prepare_images()

        # 显示图片
        if curr == STAGE.IDENTIFYING_OBJECTS:
            identifying_objects()

        # 用户指认物品完成, 开始准备查找
        if curr == STAGE.OBJECT_IDENTIFIED:
            search()

        # clip object lost scenario video
        if curr == STAGE.CLIP_VIDEO:
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
        st.session_state[SESSION_KEYS.STAGE] = STAGE.SEARCHING_COMPLETED
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.NO_RESULTS
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


def search():
    video_path, result_dir = get_resource_dir(st)
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
        st.session_state[SESSION_KEYS.STAGE] = STAGE.CLIP_VIDEO
        st.rerun()
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.NO_RESULTS


def prepare_images():
    show_assistant_animation_message("正在准备图片")
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
            st.session_state[SESSION_KEYS.STAGE] = STAGE.NO_RESULTS
            st.rerun()
        identified_objects = yolo_find_objects_by_images(
            yolo_identifying_callback, None, result_dir, None, 0.2, True
        )
        st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = identified_objects
        st.session_state[SESSION_KEYS.STAGE] = STAGE.IDENTIFYING_OBJECTS
    else:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.NO_RESULTS
    st.rerun()


def identifying_objects():
    identify_objects = st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS]

    if len(identify_objects) == 0:
        st.session_state[SESSION_KEYS.STAGE] = STAGE.NO_RESULTS
        st.rerun()
    video_dir, result_dir = get_resource_dir(st)
    files = list_image_files(result_dir)
    with st.chat_message("assistant"):
        image_cols = st.columns(2)
        with image_cols[0]:
            st.image(
                    os.path.join(result_dir, files[0]),
                    caption="请在图中确认你的物品",
                    use_container_width=True,
                )
        with image_cols[1]:
            options = []
            obj = identify_objects[0]
            for box in obj["boxes"]:
                options.append(f"{box['box_index']}-{box['label']}")
            st.radio(
                label="图片中物件列表",
                options=options,
                horizontal=False,
                key=SESSION_KEYS.USER_OBJECT_BOX_INDEX,
            )
            if st.button("确认", type="primary"):
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
                st.session_state[SESSION_KEYS.STAGE] = STAGE.OBJECT_IDENTIFIED
                st.rerun()


def yolo_identifying_callback(placeholder, file_name):
    pass


def on_extracting(placeholder, index, total):
    pass


def set_start_time():
    show_assistant_animation_message("请设置开始查找时间.")

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
        if st.button("时间确认", type='primary'):
            append_asistant_message(f"视频查找从第{st.session_state[SESSION_KEYS.START_TIME]}分钟开始")
            st.session_state[SESSION_KEYS.STAGE] = STAGE.PREPARE_IMAGES
            st.rerun()

