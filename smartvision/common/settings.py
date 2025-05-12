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
    FILTERED_OBJECTS = "filterd_objects"
    AI_RUNNING = "ai_running"
    USER_INPUT_TEXT = "user_input_text"
    USER_OBJECT_BOX_INDEX ="user_object_box_index"
    USER_OBJECT_BOX ="user_object_box"
    USER_OBJECT_CLIP_TIME = "user_object_clip_time"
    TRANSACTION_ID = "transaction_id"
    VIDEOS = "videos"


class STAGE:

    INIT = 101 # 初始化
    READY_FOR_INQUIRING = 102 # 准备询问
    INQUIRING_COMPLETED = 103 # 询问完成
    SHOW_PROMPT_UPLOADING_VIDEO  = 104 # 显示上传视频提示
    GET_VIDEO_INFO = 105 # 获取视频信息
    SHOW_PROMPT_SETTING_START_TIME = 106 # 显示设置开始时间提示
    USER_SETTING_START_TIME = 107 # 用户设置开始时间
    START_TIME_COMPLETED = 108 # 用户设置开始时间完成
    SHOW_SEARCHING_PROMPT = 109 # 显示查找提示
    SEARCHING = 110 # 正在查找
    SEARCHING_COMPLETED = 111 # 查找完成

    # 查找过程
    EXTRACTIING_IMAGES = 200
    SHOW_PROPMT_IDENTIFY_OBJECTS = 201
    IDENTIFING_OBJECTS = 202

    # 查找物品
    CUSTOMER_PREPARE_OBJECTS = 300 # 根据用户设定的开始时间，准备图片给用户指认物品位置
    SHOW_PROMPT_PREPARING_IMAGES = 301
    CUSTOMER_IDENTIFYING_OBJECTS = 302 # 用户完成对物品的指认
    CUSTOMER_OBJECT_IDENTIFIED = 304 # 用户完成对物品的指认
    CUSTOMER_VIDEO_CLIPPED = 305 # 完成对失物场景的视频剪切
    CUSTOMER_IDENTIFIED_LOST_OBJECT = 306 # 用户完成对物品的指认

    # 阿里云处理过程.
    ALIYUN_SHOW_UPLOADING_PROMPT = 500
    ALIYUN_UPLOADING_OBJECTS = 501
    ALIYUN_OBJECTS_UPLOADED = 502
    COMPLETED_NO_RESULTS = 999  # 完成，没有结果


class DATA_OPTIONS:
    FUNCTIONS = ["宠物", "物品", "剐蹭"]


class PROMPT_TEXT:
    AI_THINKING = "AI助手正在思考中..."
    WAITING_FOR_VIDEOES = "请上传视频文件，我们将协助查找..."
    IDENTIFING_OBJECT = "正在识别目标"
    UPLOADING_IDENTIFIED_OBJECTS = "正在上传已识别的目标"
    STAFF_UPLOADING_VIDEO = "请上传监控视频，方便我们定位您的物品."


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

