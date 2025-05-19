from loguru import logger
import streamlit as st
from streamlit_carousel import carousel
from common.settings import SESSION_KEYS, PROMPT_TEXT, STAGE, KEY_NAMES
from common.loader import show_md_content
from common.aliyun import put_identified_objects
from ui.components.pet.info import render_pet_info_col_info
from common.utils import get_resource_dir
from ui.components.common import append_asistant_message, append_user_message, show_assistant_animation_message

from ai.pet.llm import (
    extract_pet_info,
    get_next_question,
    initialize_chat,
)
from ai.common.yolo import yolo_find_objects_by_video

def render_pet_col_chat(chat_col, info_col):
    logger.debug("render chat info.")

    curr = st.session_state[SESSION_KEYS.STAGE]
    if curr == STAGE.NO_RESULTS:
        st.markdown("""### 谢谢您使用助手，本次会话结束, 祝你生活愉快!""")
        st.rerun()

    # 初始化对话（如果尚未初始化）
    if not st.session_state[SESSION_KEYS.INITIALIZED]:
        welcome_message = "您好！我是宠物寻找助手, 请告诉您的宠物有关特征"
        initialize_chat(st, welcome_message)

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
        # 识别目标
        if curr == STAGE.SEARCHING:
            show_assistant_animation_message("正在进行视频内容检测...")
            logger.debug("正在进行视频检测.")
            with st.chat_message("assistant"):
                placeholder = st.empty()
                searching(placeholder)

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
    logger.debug(extracted_info)
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

def searching(placeholder):
    pet_type = st.session_state[SESSION_KEYS.PET_INFO]["pet_type"]
    object_name = ""
    if "狗" in pet_type:
        object_name = "dog"
    if "猫" in pet_type:
        object_name = "cat"

    if object_name == "":
        return
        
    video_dir, image_dir = get_resource_dir(st)
    # 查找
    results = yolo_find_objects_by_video(
        video_dir= video_dir,
        image_dir= image_dir,
        object_name= object_name,
        min_confidence= 0.1,
        draw_box= False,
        callback= on_identifying_object,
        placeholder= placeholder
    )

    st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = results
    found = len(results)
    if found == 0:
        append_asistant_message(f"未找到相关内容")
    else:
        append_asistant_message(f"找到{found}个画面包含{pet_type}")

    st.session_state[SESSION_KEYS.SEARCH_RESULTS] = results
    append_asistant_message(f"过滤出置信度最高的{len(results)}个画面")
    # 显示图片
    st.session_state[SESSION_KEYS.STAGE] = STAGE.SEARCHING_COMPLETED
    st.rerun()


def on_identifying_object(placeholder, text):
    placeholder.markdown(text, unsafe_allow_html=True)


def check_info_complete():
    """检查宠物信息是否完整"""
    pet_info = st.session_state[SESSION_KEYS.PET_INFO]
    required_fields = ["pet_type", "breed", "color", "last_seen_time", "valid"]
    for field in required_fields:
        value = pet_info[field]
        if not value:
            return False
    pet_info = st.session_state[SESSION_KEYS.PET_INFO]
    return True


def update_pet_info(new_info):
    """更新宠物信息"""
    if not new_info:
        return
    for key, value in new_info.items():
        if value:  # 只更新非空值
            logger.debug(f">> {value}")
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
