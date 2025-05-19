# -*- coding: utf-8 -*-:w
class SESSION_KEYS:
    COLLECTION_COMPLETE = "collection_complete"
    INITIALIZED = "initialized"
    USER_INPUT_KEY = "user_input_key"
    PROCESSING = "processing"
    STAGE = "stage"
    READY_FOR_UPLOADING_VIDEO = "ready_for_uploading_video"
    VIDEO_UPLOADED = "video_uploaded"
    START_TIME = "start_time"
    UPLOADED_FILES = "uploaded_files"
    CHOOSE_START_TIME = "choose_start_time"
    SEARCHING = "SEARCHING"
    HIDE_CONVERSATION = "hide_conversation"
    HIDE_PROMPT = "hide_prompt"
    MESSAGES = "messages"
    PET_INFO = "pet_info"
    PROMPT_LOADING_MSG = "msg_prompt"
    BIZ_INDEX = "biz_index"
    EXTRACTING_IMAGE_MESSAGE = "extraction_message"
    INDENTIFIED_OBJECTS = "identified_objects"
    B2_RESULTS = "b2_results"
    PREPARED_DATA = "prepared_data"
    SEARCH_RESULTS = "filterd_objects"
    AI_RUNNING = "ai_running"
    USER_INPUT_TEXT = "user_input_text"
    USER_OBJECT_BOX_INDEX ="user_object_box_index"
    USER_OBJECT_BOX ="user_object_box"
    USER_OBJECT_CLIP_TIME = "user_object_clip_time"
    TRANSACTION_ID = "transaction_id"
    VIDEOS = "videos"


class STAGE:

    """
        第一阶段，视频资料准备以及宠物类的AI对话
    """
    INIT = 101 # 初始化
    # 准备询问
    READY_FOR_INQUIRING = 102 
    # 询问完成
    INQUIRING_COMPLETED = 103 
    # 显示上传视频提示
    UPLOADING_VIDEO  = 104 
    # 视频上传完成，不能更改业务类型
    VIDEO_UPLOADED = 105
    # 获取视频信息
    GET_VIDEO_INFO = 106


    """
        第二阶段，支付费用
    """
    # 产生支付二维码
    GEN_PAYMENT_QR_CODE = 201
    # 刷新页面

    """
        第3阶段，定位视频中的物件
    """
    # 显示设置开始时间提示
    SETTING_START_TIME = 310
    START_TIME_COMPLETED = 311 # 用户设置开始时间完成
    PREPARE_IMAGES = 320 # 抽取视频中的图片，供用户确认.
    IDENTIFYING_OBJECTS = 330 # 用户正在对物品的指认
    OBJECT_IDENTIFIED = 331 # 用户完成对物品的指认

    """
        第4阶段, 执行查找
    """
    SEARCHING = 401 # 正在查找
    CLIP_VIDEO = 402 # 剪切视频
    SEARCHING_COMPLETED = 403 # 查找完成
    NO_RESULTS = 404  # 完成，没有结果


class DATA_OPTIONS:
    FUNCTIONS = ["宠物寻迹", "物品追踪", "碰撞检测"]


class PROMPT_TEXT:
    AI_THINKING = "AI助手正在思考中..."
    WAITING_FOR_VIDEOES = "请上传视频文件，我们将协助查找..."
    IDENTIFING_OBJECT = "正在识别目标"
    UPLOADING_IDENTIFIED_OBJECTS = "正在上传已识别的目标"
    STAFF_UPLOADING_VIDEO = "请告诉我们从视频的什么时间开始进行查找."


class KEY_NAMES:
    OPENAI = "OPENAI_API_KEY"
    DEEPSEEK = "DEEPSEEK_API_KEY"
    MD_LOADING_ANIMATION = "loading_animation"
    FILE_LOADING_ANIMATION = "loading_animation.md"
    ALIYUN_OSS = "https://smart-vision.oss-cn-shanghai.aliyuncs.com/"


class MODEL_NAMES:
    DP_CHAT = "deepseek-chat"
    DP_REASONER = "deepseek-reasoner"
    YOLO_11X = "/opt/models/yolo/yolo11x.pt"
    YOLO_11N = "/opt/models/yolo/yolo11n.pt"
    YOLO_08X = "/opt/models/yolo/yolov8x.pt"


class LOCAL_DIRS:
    TMP_DIR = "/var/tmp/smart-vision"

