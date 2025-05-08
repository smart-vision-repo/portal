import streamlit as st
from common.settings import SESSION_KEYS
from common.settings import DATA_OPTIONS 
from common.session import reset

def render_sidebar():

    """Render the sidebar component with all its elements"""

    with st.sidebar:
        selected_option = st.radio("请选择", DATA_OPTIONS.FUNCTIONS)
        if selected_option:
            selected_index = DATA_OPTIONS.FUNCTIONS.index(selected_option)
            biz_name = DATA_OPTIONS.FUNCTIONS[selected_index]
            st.write(f"您选择的是：{selected_option}")
            pet_info = st.session_state[SESSION_KEYS.PET_INFO]
            pet_info['pet_type'] = biz_name
            st.session_state[SESSION_KEYS.PET_INFO] = pet_info
            st.session_state[SESSION_KEYS.BIZ_INDEX] =  selected_index
        else:
            st.write("您尚未选择任何选项")
        
        btn_start_conversation = st.button("开始新的对话", type='primary')
        
        if btn_start_conversation: 
            reset(st)
            st.rerun()

        st.markdown("#### 历史会话")