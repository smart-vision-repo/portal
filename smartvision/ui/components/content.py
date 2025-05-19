import os
import streamlit as st
from common.session import SESSION_KEYS
from common.settings import DATA_OPTIONS
from loguru import logger
from streamlit_player import st_player


from ui.components.pet.chat import render_pet_col_chat
from ui.components.staff.chat import render_staff_col_chat
from ui.components.collision.chat import render_collision_col_chat
from common.settings import SESSION_KEYS, STAGE, KEY_NAMES
from common.utils import get_str_time, get_resource_dir

def render_content():
    biz_index = st.session_state[SESSION_KEYS.BIZ_INDEX]
    biz_name = DATA_OPTIONS.FUNCTIONS[biz_index]
    header_string = f"我是{biz_name}寻找助手"
    curr = st.session_state[SESSION_KEYS.STAGE]
    # 显示结果
    if curr == STAGE.SEARCHING_COMPLETED:
        if biz_index == 0:
            st.subheader("宠物图片与出现时间.")
            show_identified_images()
                # play object lost scenario video
        if biz_index == 1:
            play_identified_video()
        
        if biz_index == 2:
            show_footages()
    else:
        # 创建两列布局
        chat_col, info_col = st.columns([3, 2])

        with chat_col:
            st.subheader("How can I help you?")
            st.header(header_string)

        if biz_index == 0:
            render_pet_col_chat(chat_col, info_col)
        elif biz_index == 1:
            render_staff_col_chat(chat_col, info_col)
        elif biz_index == 2:
            render_collision_col_chat(chat_col, info_col)

def show_footages():
    results = st.session_state[SESSION_KEYS.B2_RESULTS] 
    if results:
        st.subheader("Top 3 closest vehicles:")
        st.subheader("平面距离检测结果")
        cols = st.columns(3)
        for i, result in enumerate(results):
            with cols[i]:
                video_file_name = result['footage_file_name']
                seconds = f"{result['seconds']:.2f}秒"
                st.video(video_file_name, autoplay=True)
                st.info(seconds)
    else:
        st.header("无数据")


def show_identified_images():
    filterd_objects = st.session_state[SESSION_KEYS.SEARCH_RESULTS]
    count = len(filterd_objects)
    if  count == 0:
        st.warning("### 很遗憾，啥都没找到...")
        return

    cols = st.columns(3, gap="small")
    col_index = 0
    for obj in filterd_objects:
        with cols[col_index % 3]:
            file_name = obj['file_name']
            st.image(file_name, caption=get_image_time(file_name=file_name))
        col_index += 1

def play_identified_video():


    video_dir, result_dir = get_resource_dir(st)
    clip_time = st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME]
    if clip_time:
        lost_time = clip_time["lost_time"]
        clip_time = st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME]
        file_name = clip_time["file_name"]
        clip_file_name = os.path.join(result_dir, file_name.split("/")[-1])
        st.subheader(f"失物被取走时间约在视频处{int(lost_time)}秒", divider=True)
        DEFAULT_WIDTH = 32
        width = st.sidebar.slider(
            label="宽度", min_value=0, max_value=100, value=DEFAULT_WIDTH, format="%d%%"
        )
        width = max(width, 0.01)
        side = max(100 - width, 0.01)
        container, _ = st.columns([width, side])
        container.video(data=clip_file_name)
    else:
        st.header("无数据.")

def get_image_time(file_name):
    prefix = file_name.split(".")[0]
    time = prefix.split("/")[-1]
    tmp = time.split("-")
    time = tmp[1:]
    return get_str_time("-".join(time))