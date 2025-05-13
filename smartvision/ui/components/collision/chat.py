import os
import logging
import sys
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, STAGE, KEY_NAMES
from common.loader import show_md_content
from common.utils import list_image_files, get_resource_dir, scroll_to_bottom_markdown, list_video_files

from ai.common.cv import cv_extract_frames, cv_clip_video
from ai.common.collision import VehicleDetectionSystem


from ui.components.staff.info import render_staff_info_col_info
from ui.components.common import show_assistant_animation_message, append_asistant_message

from ai.pet.llm import  initialize_chat

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()

def render_collision_col_chat(chat_col, info_col):
    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.COMPLETED_NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()

    # 创建两列布局
    # chat_col, info_col = st.columns([3, 2])

    # 左侧聊天区域
    with chat_col:
        if not st.session_state[SESSION_KEYS.INITIALIZED]:
            welcome_message = "您好！我是碰撞检测助手，请您上传监控视频."
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
            scroll_to_bottom_markdown(st)

        # 准备图片，用于用户指认物品.
        if curr == STAGE.CUSTOMER_PREPARE_OBJECTS:
            prepare_images()

        # 显示图片
        if curr == STAGE.CUSTOMER_IDENTIFYING_OBJECTS:
            identifying_objects()

        # 用户指认物品完成, 开始准备查找
        if curr == STAGE.CUSTOMER_IDENTIFIED_LOST_OBJECT:
            show_searching_prompt()


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
    show_assistant_animation_message("正在查找距离您的车辆最近的目标, 请稍后...")
    video_path, result_dir = get_resource_dir(st)
    files = list_video_files(video_path)
    video_file_name = f"{video_path}/{files[0]}"
    prepared_data  = st.session_state[SESSION_KEYS.PREPARED_DATA]
    seconds = st.session_state[SESSION_KEYS.START_TIME]
    vehicle_index = st.session_state[SESSION_KEYS.USER_OBJECT_BOX_INDEX]
    vehicles = prepared_data['vehicles']
    selected_vehicle = next((v for v in vehicles if v["vehicle_id"] == vehicle_index), None)
    collision = VehicleDetectionSystem(model_path="/opt/models/yolo/yolo11x.pt", output_dir= result_dir)
    clips = collision.nearest_distance_detection(video_file_name, selected_vehicle, seconds)
    st.session_state[SESSION_KEYS.B2_RESULTS] = clips
    st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_OBJECT_IDENTIFIED
    st.rerun()
    


def prepare_images():
    show_assistant_animation_message("正在抽取视频中的图片，供您标定目标车辆")
    video_path, result_dir = get_resource_dir(st)
    start_time = st.session_state[SESSION_KEYS.START_TIME]
    videos = list_video_files(video_path)
    if len(videos) < 1: 
        return 

    video_file_name = f"{video_path}/{videos[0]}"
    collision = VehicleDetectionSystem(model_path="/opt/models/yolo/yolo11x.pt", output_dir= result_dir)
    image_file, vehicles = collision.get_vehicle_annotation_data(video_file_name, int(start_time))
    prepared_data = {"image_file": image_file, "vehicles": vehicles}
    st.session_state[SESSION_KEYS.PREPARED_DATA] = prepared_data
    st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_IDENTIFYING_OBJECTS
    st.rerun()
   

def identifying_objects():
    show_assistant_animation_message("请识别图片中的物件，点击可放大...")
    prepared_data  = st.session_state[SESSION_KEYS.PREPARED_DATA]
    image_file = prepared_data['image_file']
    vehicles = prepared_data['vehicles']
    vehicle_ids = [v['vehicle_id'] for v in vehicles]   
    with st.chat_message("assistant"):
        cols = st.columns(2)
        with cols[0]:
            st.image(image_file)
        with cols[1]:
            selected_index = st.radio("请选择", vehicle_ids, horizontal=True)
            if st.button("请确认", type='primary', use_container_width=True):
                append_asistant_message(f"您选择了图片中的第{selected_index}车")
                st.session_state[SESSION_KEYS.USER_OBJECT_BOX_INDEX] =  selected_index + 1
                st.session_state[SESSION_KEYS.STAGE] = STAGE.CUSTOMER_IDENTIFIED_LOST_OBJECT
                st.rerun()

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
