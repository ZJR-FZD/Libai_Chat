import os
from dotenv import load_dotenv
from types import SimpleNamespace

# 加载环境变量
load_dotenv()

# API配置
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_API_URL = os.getenv("QWEN_API_URL")
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME")

# 语音配置
ASR_MODEL = os.getenv("ASR_MODEL")
TTS_MODEL = os.getenv("TTS_MODEL")

# 音频文件配置
AUDIO_DIR = os.getenv("AUDIO_DIR")
USER_AUDIO_PREFIX = os.getenv("USER_AUDIO_PREFIX")
AI_AUDIO_PREFIX = os.getenv("AI_AUDIO_PREFIX")
AUDIO_FORMAT = os.getenv("AUDIO_FORMAT")

# 对话配置
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", 10))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))    

# 创建settings对象
settings = SimpleNamespace(
    QWEN_API_KEY=QWEN_API_KEY,
    QWEN_API_URL=QWEN_API_URL,
    QWEN_MODEL_NAME=QWEN_MODEL_NAME,
    ASR_MODEL=ASR_MODEL,
    TTS_MODEL=TTS_MODEL,
    AUDIO_DIR=AUDIO_DIR,
    USER_AUDIO_PREFIX=USER_AUDIO_PREFIX,
    AI_AUDIO_PREFIX=AI_AUDIO_PREFIX,
    AUDIO_FORMAT=AUDIO_FORMAT,
    MAX_HISTORY_LENGTH=MAX_HISTORY_LENGTH,
    TEMPERATURE=TEMPERATURE
)