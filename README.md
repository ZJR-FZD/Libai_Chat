# 李白人工智能体
## 需求说明
调用Qwen的任意开源版本，仿豆包、通义等实现：从web前端定制新增可实时双向语音电话的角色扮演智能体，如让李白智能体始终以李白身份与用户进行语音电话。智能体说话时可被用户语音打断（因为本地性能不够，选用调用API的方式

## 技术链说明
### 语音识别（ASR）：
利用 Whisper 库实现语音识别功能，将用户的语音输入转换为文本。对音频数据进行预处理，确保识别的准确性和稳定性。
### 大语言模型（LLM）：
定制基于 Qwen 模型的李白角色，通过设置特定的系统提示和对话历史，使智能体能够以李白的风格进行回复，并能够记忆多轮对话。
### 语音合成（TTS）：
使用 edge-tts 将 LLM 生成的文本转换为音频，并在前端播放。对音频进行后处理，如调整音量、添加音效等，提升语音的自然度和表现力。
### 模块化设计：
将所有功能模块抽象成类，提高代码的复用性和可维护性。便于定制不同风格的聊天智能体。


## 代码结构说明
```
李白语音智能体/
├── audio_files/
├── backend/
│   ├── __init__.py
│   ├── main.py                # FastAPI 启动入口（有两个版本，一个静态对话，一个动态实时语音通话，因为动态的还有bug，所以先用静态的进行展示）
│   ├── models/                # 模型相关
│   │   ├── __init__.py
│   │   └── load_model.py      # 模型加载逻辑（Qwen）
│   ├── speech/                # 语音处理模块
│   │   ├── __init__.py
│   │   ├── asr.py             # ASR：语音转文本（Whisper）
│   │   ├── tts.py             # TTS：文本转语音（Edge-tts）
│   │   └── audio_processing.py # 音频格式转换、合并、清理
│   ├── dialog/                # 对话管理模块
│   │   ├── __init__.py
│   │   ├── dialog_manager.py  # 对话管理（集成控制角色风格、多轮对话功能）
│   │   ├── conversation_history.py # 上下文记录与截断
│   │   └── prompt_templates.py # Prompt 模板
│   ├── utils/                 # 工具类模块
│   │   ├── __init__.py
│   │   ├── file_utils.py      # 音频文件存储/清理
│   │   └── thread_utils.py    # 音频处理线程/多任务
│   ├── test_***.py            # 测试文件
│   ├── websocket_server.py    # 实时通信服务：支持语音打断
│   ├── config.py              # 从 .env 加载配置
│   └── .env                   # 环境变量文件（模型路径、TTS配置等）
├── frontend/
│   ├── index.html             # 主页面
│   ├── styles.css             # 页面样式
│   ├── scripts.js             # JS逻辑：采集语音、播放TTS、WebSocket通信
└── requirements.txt           # 后端Python依赖
```

# 音频格式的转换流程

```
[麦克风输入]
↓ (Float32 PCM, 48kHz or default)
[前端 JavaScript 处理]
↓（转换为 PCM16, 16kHz）
[WebSocket 发送]
↓
[后端 FastAPI 接收]
↓
[ASR + LLM 生成文本回应]
↓
[TTS 合成音频]
↓
[WebSocket 发送回前端]
↓ (Int16 → Float32)
[AudioBuffer 播放]
↓
[音箱播放]
