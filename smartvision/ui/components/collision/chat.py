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
from ui.components.common import show_assistant_animation_message, append_asistant_message, show_assistant_messages

from ai.pet.llm import  initialize_chat

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()

def render_collision_col_chat(chat_col, info_col):
    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()

    # 创建两列布局
    # chat_col, info_col = st.columns([3, 2])

    # 左侧聊天区域
    with chat_col:
        if not st.session_state[SESSION_KEYS.INITIALIZED]:
            welcome_message = "您好！我是碰撞检测助手，请您上传监控视频."
            initialize_chat(st, welcome_message)
            st.session_state[SESSION_KEYS.STAGE] = STAGE.UPLOADING_VIDEO
        # 显示对话历史
        chat_container = st.container()
        show_assistant_messages(chat_container)


        if curr == STAGE.SETTING_START_TIME:
            set_start_time()

        # 准备图片，用于用户指认物品.
        if curr == STAGE.PREPARE_IMAGES:
            prepare_images()

        # 显示图片
        if curr == STAGE.IDENTIFYING_OBJECTS:
            identifying_objects()

        # 用户指认物品完成, 开始准备查找
        if curr == STAGE.SEARCHING:
            searching()


    render_staff_info_col_info(info_col)

def on_searching_callback():
    pass


def searching():
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
    st.session_state[SESSION_KEYS.STAGE] = STAGE.SEARCHING_COMPLETED
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
    st.session_state[SESSION_KEYS.STAGE] = STAGE.IDENTIFYING_OBJECTS
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
                st.session_state[SESSION_KEYS.STAGE] = STAGE.SEARCHING
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
        seconds = st.session_state[SESSION_KEYS.START_TIME]
        st.info(f"物品的最后发现时间在视频的{seconds}秒处")
        if st.button("确认"):
            st.session_state[SESSION_KEYS.STAGE] = STAGE.PREPARE_IMAGES
            st.rerun()
