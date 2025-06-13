import io
import torch
import whisper
import numpy as np
import ffmpeg
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from backend.speech.asr import ASR
from backend.speech.tts import TTSGenerator
from backend.dialog.dialog_manager import DialogManager
import uvicorn
import asyncio
import os

app = FastAPI(title="与李白聊天")

# 初始化组件
asr = ASR()
tts = TTSGenerator()
dialog_manager = DialogManager()

# 历史对话记录
history = []

# API端点 - 处理文件上传并进行语音识别
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """接收音频文件并返回识别结果"""
    audio_data = await file.read()
    text = asr.transcribe(audio_data)
    if text:
        history.append({"user": text})
        return {"text": text}
    else:
        raise HTTPException(status_code=500, detail="语音识别失败")

# WebSocket端点 - 生成LLM回复并进行TTS
@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            dialog_manager.add_user_message(text)
            output_text = dialog_manager.generate_response()
            history[-1]["li_bai"] = output_text
            
            # 生成完整音频
            wav_data = await tts.synthesize_full_audio(output_text)
            
            # 发送完整音频数据
            await websocket.send_json({"text": output_text})
            await websocket.send_bytes(wav_data)
            
    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        await websocket.close(code=1011)

# 主页 - 返回聊天界面
@app.get("/", response_class=HTMLResponse)
async def index():
    history_html = ""
    for chat in history:
        if "user" in chat:
            history_html += f"<p>我：{chat['user']}</p>"
        if "li_bai" in chat:
            history_html += f"<p>李白：{chat['li_bai']}</p>"

    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>来和李白聊天吧</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; }}
        button {{ padding: 12px 24px; font-size: 16px; margin: 10px; cursor: pointer; }}
        #result {{ margin-top: 20px; padding: 10px; min-height: 40px; border: 1px solid #ddd; }}
        #history {{ margin-top: 20px; text-align: left; max-height: 300px; overflow-y: auto; }}
        .btn-primary {{ background-color: #4CAF50; color: white; border: none; border-radius: 4px; }}
        .btn-primary:hover {{ background-color: #45a049; }}
        .btn-secondary {{ background-color: #f44336; color: white; border: none; border-radius: 4px; }}
        .btn-secondary:hover {{ background-color: #d32f2f; }}
    </style>
</head>
<body>
    <h3>来和李白聊天吧</h3>
    <button id="record-btn" class="btn-primary">开始录音</button>
    <button id="stop-btn" disabled class="btn-secondary">停止并识别</button>
    <div id="status">状态: 准备就绪</div>
    <div id="result">识别结果将显示在这里...</div>
    <div id="history">
        {history_html}
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const recordBtn = document.getElementById('record-btn');
            const stopBtn = document.getElementById('stop-btn');
            const statusEl = document.getElementById('status');
            const resultEl = document.getElementById('result');
            const historyEl = document.getElementById('history');
            
            let mediaRecorder = null;
            let audioChunks = [];
            let isRecording = false;
            let audioContext = null;
            let currentAudioSource = null;
            let wsConnection = null;
            
            // 检查浏览器支持
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                statusEl.textContent = "状态: 浏览器不支持录音功能";
                recordBtn.disabled = true;
                return;
            }}
            
            // 初始化音频上下文
            function initAudioContext() {{
                if (!audioContext) {{
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }}
                return audioContext;
            }}
            
            // 开始录音
            recordBtn.addEventListener('click', function() {{
                // 停止当前播放的音频
                stopCurrentAudio();
                
                // 关闭现有WebSocket连接
                closeWebSocket();
                
                startRecording();
            }});
            
            // 停止录音
            stopBtn.addEventListener('click', function() {{
                stopRecording();
            }});
            
            function stopCurrentAudio() {{
                if (currentAudioSource) {{
                    try {{
                        currentAudioSource.stop();
                    }} catch (e) {{
                        console.log("停止音频失败:", e);
                    }}
                    currentAudioSource = null;
                }}
            }}
            
            function closeWebSocket() {{
                if (wsConnection && wsConnection.readyState !== WebSocket.CLOSED) {{
                    wsConnection.close();
                    wsConnection = null;
                }}
            }}
            
            async function startRecording() {{
                try {{
                    statusEl.textContent = "状态: 正在录音...";
                    recordBtn.disabled = true;
                    stopBtn.disabled = false;
                    
                    const stream = await navigator.mediaDevices.getUserMedia({{ 
                        audio: {{
                            sampleRate: 44100,
                            channelCount: 1,
                            noiseSuppression: true,
                            echoCancellation: true
                        }}
                    }});
                    
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = e => {{
                        audioChunks.push(e.data);
                    }};
                    
                    mediaRecorder.onstop = () => {{
                        statusEl.textContent = "状态: 正在发送识别...";
                        const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                        sendAudioToServer(audioBlob);
                        
                        // 释放麦克风资源
                        stream.getTracks().forEach(track => track.stop());
                    }};
                    
                    mediaRecorder.start();
                    isRecording = true;
                }} catch (error) {{
                    console.error("录音错误:", error);
                    statusEl.textContent = "状态: 录音失败，请重试";
                    recordBtn.disabled = false;
                    stopBtn.disabled = true;
                }}
            }}
            
            function stopRecording() {{
                if (mediaRecorder && mediaRecorder.state !== "inactive") {{
                    statusEl.textContent = "状态: 停止录音...";
                    mediaRecorder.stop();
                    isRecording = false;
                }}
            }}
            
            async function sendAudioToServer(audioBlob) {{
                try {{
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.wav');
                    
                    const response = await fetch('/api/transcribe', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    if (response.ok) {{
                        const data = await response.json();
                        resultEl.textContent = "识别结果: " + data.text;
                        statusEl.textContent = "状态: 正在生成回复...";
                        connectWebSocket(data.text);
                    }} else {{
                        try {{
                            const errorData = await response.json();
                            resultEl.textContent = "识别结果: 失败 (" + errorData.detail + ")";
                        }} catch (e) {{
                            resultEl.textContent = "识别结果: 失败 (服务器错误)";
                        }}
                        statusEl.textContent = "状态: 服务器错误 " + response.status;
                    }}
                }} catch (error) {{
                    console.error("发送错误:", error);
                    resultEl.textContent = "识别结果: 失败 (网络错误)";
                    statusEl.textContent = "状态: 网络错误，请检查后端连接";
                }} finally {{
                    recordBtn.disabled = false;
                    stopBtn.disabled = true;
                }}
            }}
            
            function addMessageToHistory(sender, message) {{
                const msgElement = document.createElement('p');
                msgElement.textContent = sender + "：" + message;  // 修正为普通字符串拼接
                historyEl.appendChild(msgElement);
                // 滚动到底部
                historyEl.scrollTop = historyEl.scrollHeight;
            }}
            
            function connectWebSocket(text) {{
                wsConnection = new WebSocket(`ws://${{location.host}}/ws/tts`);
                wsConnection.binaryType = "arraybuffer";
                
                wsConnection.onopen = () => {{
                    statusEl.textContent = "状态: 正在连接服务器...";
                    wsConnection.send(text);
                }};
                
                let receivedText = null;
                
                wsConnection.onmessage = async (event) => {{
                    if (typeof event.data === 'string') {{
                        // 接收文本消息
                        const data = JSON.parse(event.data);
                        receivedText = data.text;
                        addMessageToHistory("李白", receivedText);
                        statusEl.textContent = "状态: 正在接收音频数据...";
                    }} else {{
                        // 接收二进制音频数据
                        if (!receivedText) {{
                            console.error("未收到文本消息");
                            return;
                        }}
                        
                        try {{
                            const audioContext = initAudioContext();
                            
                            // 解码音频数据
                            const audioBuffer = await audioContext.decodeAudioData(event.data);
                            
                            // 播放音频
                            statusEl.textContent = "状态: 准备播放...";
                            playAudioBuffer(audioContext, audioBuffer);
                            
                        }} catch (error) {{
                            console.error("解码音频失败:", error);
                            statusEl.textContent = "状态: 音频播放失败";
                        }}
                    }}
                }};
                
                wsConnection.onclose = (event) => {{
                    if (event.wasClean) {{
                        statusEl.textContent = "状态: WebSocket连接已关闭";
                    }} else {{
                        statusEl.textContent = "状态: WebSocket连接意外断开";
                    }}
                    wsConnection = null;
                }};
                
                wsConnection.onerror = (e) => {{
                    console.error("WebSocket错误:", e);
                    statusEl.textContent = "状态: WebSocket连接错误";
                    wsConnection = null;
                }};
            }}
            
            async function playAudioBuffer(audioContext, audioBuffer) {{
                stopCurrentAudio();
                
                // 恢复音频上下文（如果被浏览器暂停）
                if (audioContext.state === 'suspended') {{
                    await audioContext.resume();
                    console.log("音频上下文已恢复");
                }}
                
                currentAudioSource = audioContext.createBufferSource();
                currentAudioSource.buffer = audioBuffer;
                currentAudioSource.connect(audioContext.destination);
                
                currentAudioSource.start();
                statusEl.textContent = "状态: 正在播放...";
                
                // 监听播放结束事件
                currentAudioSource.onended = () => {{
                    statusEl.textContent = "状态: 播放完成";
                    currentAudioSource = null;
                }};
                
                // 监听播放错误事件
                currentAudioSource.onerror = (e) => {{
                    console.error("音频播放错误:", e);
                    statusEl.textContent = "状态: 播放过程中出错";
                    currentAudioSource = null;
                }};
            }}
        }});
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)