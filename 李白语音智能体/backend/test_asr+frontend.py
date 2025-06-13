import io
import torch
import whisper
import numpy as np
import ffmpeg
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from backend.speech.asr import ASR
import uvicorn

app = FastAPI(title="语音识别API")

# 初始化ASR实例
asr = ASR()

# API端点 - 处理文件上传
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """接收音频文件并返回识别结果"""
    audio_data = await file.read()
    text = asr.transcribe(audio_data)
    return {"text": text}

# 主页 - 返回简单的测试界面
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>语音识别测试</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
        button { padding: 12px 24px; font-size: 16px; margin: 10px; }
        #result { margin-top: 20px; padding: 10px; min-height: 40px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h3>语音识别测试</h3>
    <button id="record-btn">开始录音</button>
    <button id="stop-btn" disabled>停止并识别</button>
    <div id="status">状态: 准备就绪</div>
    <div id="result">识别结果将显示在这里...</div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const recordBtn = document.getElementById('record-btn');
            const stopBtn = document.getElementById('stop-btn');
            const statusEl = document.getElementById('status');
            const resultEl = document.getElementById('result');
            
            let mediaRecorder = null;
            let audioChunks = [];
            let isRecording = false;
            
            // 检查浏览器支持
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                statusEl.textContent = "状态: 浏览器不支持录音功能";
                recordBtn.disabled = true;
                return;
            }
            
            // 开始录音
            recordBtn.addEventListener('click', function() {
                startRecording();
            });
            
            // 停止录音
            stopBtn.addEventListener('click', function() {
                stopRecording();
            });
            
            async function startRecording() {
                try {
                    statusEl.textContent = "状态: 正在录音...";
                    recordBtn.disabled = true;
                    stopBtn.disabled = false;
                    
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = e => {
                        audioChunks.push(e.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        statusEl.textContent = "状态: 正在发送识别...";
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        sendAudioToServer(audioBlob);
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                } catch (error) {
                    console.error("录音错误:", error);
                    statusEl.textContent = "状态: 录音失败，请重试";
                    recordBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            }
            
            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    statusEl.textContent = "状态: 停止录音...";
                    mediaRecorder.stop();
                    isRecording = false;
                }
            }
            
            async function sendAudioToServer(audioBlob) {
                try {
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.wav');
                    
                    const response = await fetch('/api/transcribe', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        resultEl.textContent = "识别结果: " + data.text;
                        statusEl.textContent = "状态: 识别完成";
                    } else {
                        resultEl.textContent = "识别结果: 失败 (服务器错误)";
                        statusEl.textContent = `状态: 服务器错误 ${response.status}`;
                    }
                } catch (error) {
                    console.error("发送错误:", error);
                    resultEl.textContent = "识别结果: 失败 (网络错误)";
                    statusEl.textContent = "状态: 网络错误，请检查后端连接";
                } finally {
                    recordBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            }
        });
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)    