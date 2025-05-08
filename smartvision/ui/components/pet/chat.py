import os
import logging
import sys
import time
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, LOCAL_DIRS, STAGE, KEY_NAMES
from common.loader import show_md_content
from common.aliyun import put_identified_objects
from ui.components.pet.info import render_pet_info_col_info
from ui.components.common import append_asistant_message, append_user_message

from ai.pet.llm import (
    extract_pet_info,
    get_next_question,
    initialize_chat,
)
from ai.common.yolo import yolo_find_objects_by_images
from ai.common.cv import cv_extract_frames

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger()


def render_pet_col_chat(chat_col, info_col):

    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.COMPLETED_NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()
    # 初始化对话（如果尚未初始化）
    if not st.session_state[SESSION_KEYS.INITIALIZED]:
        welcome_message = "您好！我是宠物寻找助手, 请告诉您的宠物有关特征"
        initialize_chat(st, welcome_message)
    # 创建两列布局
    # chat_col, info_col = st.columns([3, 2])

    # 左侧聊天区域
    with chat_col:
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
            with st.chat_message("assistant"):
                show_md_content(
                    st,
                    KEY_NAMES.FILE_LOADING_ANIMATION,
                    st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG],
                )

        # 抽取图片
        if curr == STAGE.EXTRACTIING_IMAGES:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                extract_video_frames(placeholder)

        # 显示作业提示
        if curr == STAGE.SHOW_PROPMT_IDENTIFY_OBJECTS:
            ready_for_identifying_object()

        # 识别目标
        if curr == STAGE.IDENTIFING_OBJECTS:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                identify_objects(placeholder)

        # 准备上传
        if curr == STAGE.ALIYUN_SHOW_UPLOADING_PROMPT:
            ready_for_uploading()

        # 正在上传
        if curr == STAGE.ALIYUN_UPLOADING_OBJECTS:
            upload_images_to_aliyun()

        # 用户输入区域
        if not st.session_state[SESSION_KEYS.COLLECTION_COMPLETE]:
            handle_user_input()
            handle_ai_running()

    render_pet_info_col_info(info_col)


def handle_ai_running():

    if not st.session_state[SESSION_KEYS.AI_RUNNING]:
        return

    user_input = st.session_state[SESSION_KEYS.USER_INPUT_TEXT]
    # 从用户消息中提取宠物信息
    extracted_info = extract_pet_info(st, user_input)
    update_pet_info(extracted_info)

    # 检查信息是否完整
    is_complete = check_info_complete()
    if is_complete:
        st.session_state[SESSION_KEYS.AI_RUNNING] = False
        st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG] = (
            PROMPT_TEXT.WAITING_FOR_VIDEOES
        )
        st.session_state[SESSION_KEYS.COLLECTION_COMPLETE] = True
        st.rerun()

    # 获取AI响应
    next_response = get_next_question(st)

    # 添加AI响应到历史记录
    append_asistant_message(next_response)

    # 重置处理状态
    st.session_state[SESSION_KEYS.PROCESSING] = False
    st.session_state[SESSION_KEYS.AI_RUNNING] = False

    # 更新输入框key以清空输入
    st.session_state[SESSION_KEYS.USER_INPUT_KEY] += 1

    # 触发页面刷新以显示新消息
    st.rerun()


def handle_user_input():
    if st.session_state[SESSION_KEYS.PROCESSING]:
        return

    user_input = st.chat_input(
        "请输入您的消息...",
        key=f"chat_input_{st.session_state[SESSION_KEYS.USER_INPUT_KEY]}",
    )

    if user_input:
        # 确保用户消息被添加到历史记录
        append_user_message(user_input)
        st.session_state[SESSION_KEYS.AI_RUNNING] = True
        st.session_state[SESSION_KEYS.PROCESSING] = True
        st.session_state[SESSION_KEYS.USER_INPUT_TEXT] = user_input
        st.rerun()


def get_resource_dir():
    video_path = (
        f"{LOCAL_DIRS.VIDEO_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}"
    )
    image_path = (
        f"{LOCAL_DIRS.IMAGE_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}"
    )
    return video_path, image_path


def extract_video_frames(placeholder):
    """
    Function: extract_video_frames
    """
    path, output_dir = get_resource_dir()
    start_time = time.time()
    summary = cv_extract_frames(
        on_extracting_images, placeholder, path, output_dir, 0, 0, 1
    )
    end_time = time.time()
    elapsed_time = end_time - start_time
    text = "视频{}个, 总时长{}秒, 图像处理用时:{}秒"
    video_count = len(summary)
    durations = sum(map(lambda x: x["duration"], summary))
    append_asistant_message(
        text.format(int(video_count), int(durations), int(elapsed_time))
    )
    st.session_state[SESSION_KEYS.STAGE] = STAGE.SHOW_PROPMT_IDENTIFY_OBJECTS
    st.rerun()


def on_extracting_images(placeholder, image_index, total):
    """
    Function: 实时显示进度
    """
    message = f"""<span>正在提取视频画面,当前进度(<span style='font-size: 20px; color=red'>{image_index/total:.2%}</span>):{image_index}/{int(total)}</span>"""
    placeholder.markdown(
        message,
        unsafe_allow_html=True,
    )


def ready_for_uploading():
    st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG] = (
        PROMPT_TEXT.UPLOADING_IDENTIFIED_OBJECTS
    )
    st.session_state[SESSION_KEYS.PROCESSING] = True
    st.session_state[SESSION_KEYS.STAGE] = STAGE.ALIYUN_UPLOADING_OBJECTS
    st.rerun()


def upload_images_to_aliyun():
    files = st.session_state[SESSION_KEYS.FILTERED_OBJECTS]
    file_names = [file["file_name"] for file in files]
    transaction_id = st.session_state[SESSION_KEYS.TRANSACTION_ID]
    put_identified_objects(transaction_id, file_names)
    st.session_state[SESSION_KEYS.PROCESSING] = False
    st.session_state[SESSION_KEYS.STAGE] = STAGE.ALIYUN_OBJECTS_UPLOADED
    st.rerun()


def ready_for_identifying_object():
    st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG] = PROMPT_TEXT.IDENTIFING_OBJECT
    st.session_state[SESSION_KEYS.PROCESSING] = True
    st.session_state[SESSION_KEYS.STAGE] = STAGE.IDENTIFING_OBJECTS
    st.rerun()


def identify_objects(placeholder):
    pet_type = st.session_state[SESSION_KEYS.PET_INFO]["pet_type"]
    object_name = ""
    if "狗" in pet_type:
        object_name = "dog"
    if "猫" in pet_type:
        object_name = "cat"

    if object_name == "":
        return

    identified_objects = yolo_find_objects_by_images(
        on_identifying_object,
        placeholder,
        f"{LOCAL_DIRS.IMAGE_DIR}/{st.session_state[SESSION_KEYS.TRANSACTION_ID]}",
        object_name,
        0.1,
    )
    st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = identified_objects
    found = len(identified_objects)
    if found == 0:
        append_asistant_message(f"未找到相关内容")
        st.session_state[SESSION_KEYS.STAGE] = STAGE.COMPLETED_NO_RESULTS
    else:
        append_asistant_message(f"找到{found}个画面包含{pet_type}")

    sorted_data = filter_identified_objects(identified_objects)
    st.session_state[SESSION_KEYS.FILTERED_OBJECTS] = sorted_data
    append_asistant_message(f"过滤出置信度最高的{len(sorted_data)}个画面")
    # 转到更新上传图片至阿里云
    st.session_state[SESSION_KEYS.STAGE] = STAGE.ALIYUN_SHOW_UPLOADING_PROMPT
    st.rerun()


def on_identifying_object(placeholder, index, total, suspectors, confidence):
    text = f"""从第**{index}/{total}**个视频中找到**{suspectors}**个宠物,相似度为**{confidence:.2%}**"""
    placeholder.markdown(text, unsafe_allow_html=True)


def onSetStartTime(start_time):
    append_asistant_message(f"你选择了从第**⏰{start_time}**分钟开始查找")
    st.session_state[SESSION_KEYS.START_TIME] = start_time
    st.session_state[SESSION_KEYS.STAGE] = STAGE.SHOW_PROPMPT_SEARCHING


def check_info_complete():
    """检查宠物信息是否完整"""
    required_fields = ["pet_type", "breed", "color", "last_seen_time"]
    for field in required_fields:
        if not st.session_state[SESSION_KEYS.PET_INFO][field]:
            return False
    return True


def update_pet_info(new_info):
    """更新宠物信息"""
    if not new_info:
        return
    for key, value in new_info.items():
        if value:  # 只更新非空值
            st.session_state[SESSION_KEYS.PET_INFO][key] = value


def filter_identified_objects(data):
    # Step 1: Extract the number from file_name
    for item in data:
        # Remove ".jpg" and split by "-"
        name_parts = item["file_name"].replace(".jpg", "").split("-")
        # Get the last segment as an integer
        item["number"] = int(name_parts[-1])
    print(data)
    # Sort data by number
    sorted_data = sorted(data, key=lambda x: x["number"])

    # Group consecutive numbers and find max confidence for each group
    result = []
    current_group = [sorted_data[0]]

    for i in range(1, len(sorted_data)):
        if sorted_data[i]["number"] == sorted_data[i - 1]["number"] + 1:
            # Numbers are consecutive, add to current group
            current_group.append(sorted_data[i])
        else:
            # Numbers are not consecutive, process current group
            max_confidence_item = max(current_group, key=lambda x: x["confidence"])
            result.append(max_confidence_item)
            # Start a new group
            current_group = [sorted_data[i]]

    # Process the last group
    max_confidence_item = max(current_group, key=lambda x: x["confidence"])
    result.append(max_confidence_item)

    return result
