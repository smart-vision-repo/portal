import os
import json
from llama_index.core.llms import ChatMessage
from llama_index.llms.deepseek import DeepSeek
from common.settings import SESSION_KEYS, KEY_NAMES, MODEL_NAMES, STAGE

DP_API_KEY = os.getenv(KEY_NAMES.DEEPSEEK)
llm = DeepSeek(model=MODEL_NAMES.DP_CHAT, request_timeout=120.0, api_key=DP_API_KEY)


def initialize_chat(st, welcome_message):

    """初始化对话"""
    system_message = """
    你是一个友好的宠物寻找助手，帮助用户收集丢失宠物的信息。
    你需要收集以下信息：宠物类型(pet_type)、品种(breed)、颜色(color)、最后见到的时间(last_seen_time)，以及任何额外信息(extra_info)。
    如果用户提供的信息不完整，请友好地询问缺失的信息。
    当所有必要信息都收集到后，总结所有信息并告知用户信息收集完成。
    """

    

    st.session_state[SESSION_KEYS.MESSAGES] = [
        {"role": "system", "content": system_message},
        {"role": "assistant", "content": welcome_message},
    ]
    st.session_state[SESSION_KEYS.INITIALIZED] = True
    st.session_state[SESSION_KEYS.STAGE] = STAGE.INIT


def get_next_question(st):
    """根据当前收集的信息，生成下一个问题"""
    pet_info = st.session_state[SESSION_KEYS.PET_INFO]
    missing_info = []

    if not pet_info["pet_type"]:
        missing_info.append("宠物类型")
    if not pet_info["breed"]:
        missing_info.append("品种")
    if not pet_info["color"]:
        missing_info.append("颜色")
    if not pet_info["last_seen_time"]:
        missing_info.append("最后见到的时间")

    current_info = {k: v for k, v in pet_info.items() if v}

    system_message = f"""
    基于已收集的宠物信息：{json.dumps(current_info, ensure_ascii=False)}
    缺失的信息有：{", ".join(missing_info) if missing_info else "无"}
    
    请生成一个友好的问题，询问用户下一个最重要的缺失信息。如果所有必要信息都已收集（宠物类型、品种、颜色、最后见到时间），
    请总结所有信息并告知用户信息收集完成，同时询问是否有任何额外信息需要补充。
    
    保持语气友好、简洁。不要使用JSON格式回复，直接用自然语言提问, 对于已经了解的答案不需要再出现在问题中。
    """

    try:

        messages = [
            ChatMessage(role="user", content=system_message),
        ]

        return llm.chat(messages).message.content

    except Exception as e:
        st.error(f"API请求错误: {str(e)}")
        return "请问还有什么关于您丢失宠物的信息可以提供吗？"


def extract_pet_info(st, text):
    """从用户输入中提取宠物信息"""
    # 构建提示以提取JSON
    prompt = f"""
    从以下文本中提取宠物信息，并以JSON格式返回。
    需要提取的字段：宠物类型(pet_type)、品种(breed)、颜色(color)、最后见到的时间(last_seen_time), 以及任何额外信息(extra_info)。
    如果某些字段在文本中没有提到，则在JSON中将该字段值设为空字符串。
    
    文本：{text}
    
    我们需要将你返回的数据解析json数据, 你是一个JSON数据生成器，必须严格按以下要求执行：
    1. 仅输出以下JSON格式内容，不要任何额外文字
    2. 所有字段必须保留，未知内容用空字符串""
    3. 禁止包含```json等代码块标记
    4. 禁止添加解释或注释
    5. 不用返回你是谁
    {{
        "pet_type": "",
        "breed": "",
        "color": "",
        "last_seen_time": "",
        "extra_info": ""，
    }}
    """

    try:
        messages = [
            ChatMessage(role="user", content=prompt),
        ]
        result = llm.chat(messages).message.content
        print(f"提取的宠物信息: {result}")
        # 尝试解析JSON
        try:
            info = json.loads(result)
            # 确保所有必要的键都存在
            required_keys = [
                "pet_type",
                "breed",
                "color",
                "last_seen_time",
                "extra_info",
            ]
            for key in required_keys:
                if key not in info:
                    info[key] = ""
            return info
        except json.JSONDecodeError:
            st.error("无法解析响应中的JSON")
            return None
    except Exception as e:
        st.error(f"API请求错误: {str(e)}")
        return None
