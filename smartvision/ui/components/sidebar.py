import streamlit as st
from common.settings import SESSION_KEYS
from common.settings import DATA_OPTIONS 
from common.session import reset

def render_sidebar():

    """Render the sidebar component with all its elements"""

    with st.sidebar:
        selected_option = st.radio("请选择", DATA_OPTIONS.FUNCTIONS)
        btn_start_conversation = st.button("开始新的对话", type='primary')
        st.markdown("#### 历史会话")
        if btn_start_conversation: 
            reset(st)
            st.rerun()
        if selected_option:
            selected_index = DATA_OPTIONS.FUNCTIONS.index(selected_option)
            st.session_state[SESSION_KEYS.BIZ_INDEX] =  selected_index