需求说明：调用Qwen的任意开源版本，仿豆包、通义等实现：从web前端定制新增可实时双向语音电话的角色扮演智能体，如让李白智能体始终以李白身份与用户进行语音电话。智能体说话时可被用户语音打断
（因为本地性能不够，选用调用API的方式）

代码结构介绍：
李白语音智能体/
├── audio_files/   
│
├── backend/              
│   ├── __init__.py            
│   ├── main.py                     # FastAPI 启动入口
│   ├── models/                     # 模型相关
│   │   ├── __init__.py
│   │   └── load_model.py           # 模型加载逻辑（Qwen-7B-Chat）
│   ├── speech/                     # 语音处理模块
│   │   ├── __init__.py
│   │   ├── asr.py                  # ASR：语音转文本（Whisper）
│   │   ├── tts.py                  # TTS：文本转语音（VITS-Mandarin）
│   │   └── audio_processing.py     # 音频格式转换、合并、清理
│   ├── dialog/                     # 对话管理模块
│   │   ├── __init__.py
│   │   ├── dialog_manager.py    # 控制“李白”人格等
│   │   ├── conversation_history.py # 上下文记录与截断
│   │   └── prompt_templates.py     # Prompt 模板（如“你是李白...”）
│   ├── utils/                      # 工具类模块
│   │   ├── __init__.py
│   │   ├── file_utils.py           # 音频文件存储/清理
│   │   └── thread_utils.py         # 音频处理线程/多任务
│   ├── test.py                     # 测试asr+llm+tts
│   │── websocket_server.py         # 实时通信服务：支持语音打断
│   ├── config.py                   # 从 `.env` 加载配置
│   └── .env                        # 环境变量文件（模型路径、TTS配置等）
│
├── frontend/                       
│   ├── index.html                  # 主页面
│   ├── styles.css                  # 页面样式
│   ├── scripts.js                  # JS逻辑：采集语音、播放TTS、WebSocket通信
│
├── requirements.txt                # 后端Python依赖
└── README.md                       # 项目说明文档

音频格式的转换：
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
