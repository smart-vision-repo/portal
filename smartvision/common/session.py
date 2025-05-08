from common.settings import SESSION_KEYS
import uuid


def reset(st):
    st.session_state[SESSION_KEYS.HIDE_PROMPT] = False

    # 初始化业务类型
    st.session_state[SESSION_KEYS.BIZ_INDEX] = 0

    st.session_state[SESSION_KEYS.PET_INFO] = {
        "pet_type": "",
        "breed": "",
        "color": "",
        "last_seen_time": "",
        "extra_info": "",
    }

    st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG] = "AI助手正在思考中..."

    st.session_state[SESSION_KEYS.COLLECTION_COMPLETE] = False

    st.session_state[SESSION_KEYS.INITIALIZED] = False

    st.session_state[SESSION_KEYS.USER_INPUT_KEY] = 0

    st.session_state[SESSION_KEYS.PROCESSING] = False

    st.session_state[SESSION_KEYS.VIDEO_UPLOADED] = False

    st.session_state[SESSION_KEYS.SEARCHING] = False

    st.session_state[SESSION_KEYS.START_TIME] = -1

    st.session_state[SESSION_KEYS.UPLOADED_FILES] = []

    st.session_state[SESSION_KEYS.EXTRACTING_IMAGE_MESSAGE] = ""

    st.session_state[SESSION_KEYS.CHOOSE_START_TIME] = False

    st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = []

    st.session_state[SESSION_KEYS.FILTERED_OBJECTS] = []

    st.session_state[SESSION_KEYS.AI_RUNNING] = False

    st.session_state[SESSION_KEYS.STAGE] = 100

    st.session_state[SESSION_KEYS.TRANSACTION_ID] = uuid.uuid4()

    st.session_state[SESSION_KEYS.MESSAGES] = []

    st.session_state[SESSION_KEYS.USER_OBJECT_BOX_INDEX] = -1

    st.session_state[SESSION_KEYS.USER_OBJECT_BOX] = {}

    st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME] = {}

    st.session_state[SESSION_KEYS.VIDEOS] = []


def init_session(st):
    # 初始化session state变量

    if SESSION_KEYS.HIDE_PROMPT not in st.session_state:
        st.session_state[SESSION_KEYS.HIDE_PROMPT] = False

    # 初始化业务类型
    if SESSION_KEYS.BIZ_INDEX not in st.session_state:
        st.session_state[SESSION_KEYS.BIZ_INDEX] = 0

    if SESSION_KEYS.PET_INFO not in st.session_state:
        st.session_state[SESSION_KEYS.PET_INFO] = {
            "pet_type": "",
            "breed": "",
            "color": "",
            "last_seen_time": "",
            "extra_info": "",
        }

    if SESSION_KEYS.PROMPT_LOADING_MSG not in st.session_state:
        st.session_state[SESSION_KEYS.PROMPT_LOADING_MSG] = "AI助手正在思考中..."

    if SESSION_KEYS.COLLECTION_COMPLETE not in st.session_state:
        st.session_state[SESSION_KEYS.COLLECTION_COMPLETE] = False

    if SESSION_KEYS.INITIALIZED not in st.session_state:
        st.session_state[SESSION_KEYS.INITIALIZED] = False

    if SESSION_KEYS.MESSAGES not in st.session_state:
        st.session_state[SESSION_KEYS.MESSAGES] = []

    if SESSION_KEYS.USER_INPUT_KEY not in st.session_state:
        st.session_state[SESSION_KEYS.USER_INPUT_KEY] = 0

    if SESSION_KEYS.PROCESSING not in st.session_state:
        st.session_state[SESSION_KEYS.PROCESSING] = False

    if SESSION_KEYS.VIDEO_UPLOADED not in st.session_state:
        st.session_state[SESSION_KEYS.VIDEO_UPLOADED] = False

    if SESSION_KEYS.SEARCHING not in st.session_state:
        st.session_state[SESSION_KEYS.SEARCHING] = False

    if SESSION_KEYS.START_TIME not in st.session_state:
        st.session_state[SESSION_KEYS.START_TIME] = -1

    if SESSION_KEYS.UPLOADED_FILES not in st.session_state:
        st.session_state[SESSION_KEYS.UPLOADED_FILES] = []

    if SESSION_KEYS.EXTRACTING_IMAGE_MESSAGE not in st.session_state:
        st.session_state[SESSION_KEYS.EXTRACTING_IMAGE_MESSAGE] = ""

    if SESSION_KEYS.CHOOSE_START_TIME not in st.session_state:
        st.session_state[SESSION_KEYS.CHOOSE_START_TIME] = False

    if SESSION_KEYS.INDENTIFIED_OBJECTS not in st.session_state:
        st.session_state[SESSION_KEYS.INDENTIFIED_OBJECTS] = []

    if SESSION_KEYS.FILTERED_OBJECTS not in st.session_state:
        st.session_state[SESSION_KEYS.FILTERED_OBJECTS] = []

    if SESSION_KEYS.AI_RUNNING not in st.session_state:
        st.session_state[SESSION_KEYS.AI_RUNNING] = False

    if SESSION_KEYS.STAGE not in st.session_state:
        st.session_state[SESSION_KEYS.STAGE] = 0

    if SESSION_KEYS.USER_OBJECT_BOX_INDEX not in st.session_state:
        st.session_state[SESSION_KEYS.USER_OBJECT_BOX_INDEX] = -1

    if SESSION_KEYS.USER_OBJECT_BOX not in st.session_state:
        st.session_state[SESSION_KEYS.USER_OBJECT_BOX] = {}

    if SESSION_KEYS.USER_OBJECT_CLIP_TIME not in st.session_state:
        st.session_state[SESSION_KEYS.USER_OBJECT_CLIP_TIME] = {}

    if SESSION_KEYS.TRANSACTION_ID not in st.session_state:
        st.session_state[SESSION_KEYS.TRANSACTION_ID] = uuid.uuid4()

    if SESSION_KEYS.VIDEOS not in st.session_state:
        st.session_state[SESSION_KEYS.VIDEOS] = []
