import streamlit as st
from common.session import SESSION_KEYS
from common.settings import DATA_OPTIONS
from ui.components.pet.chat import render_pet_col_chat
from ui.components.staff.chat import render_staff_col_chat


def render_content():
    biz_index = st.session_state[SESSION_KEYS.BIZ_INDEX]
    biz_name = DATA_OPTIONS.FUNCTIONS[biz_index]
    header_string = f"我是{biz_name}寻找助手"

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
        pass
