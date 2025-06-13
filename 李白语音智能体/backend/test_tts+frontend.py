import io
import wave
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
import edge_tts
import uvicorn
from backend.speech.tts import TTSGenerator

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return HTMLResponse(html_content)

@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    await websocket.accept()
    tts = TTSGenerator()
    try:
        while True:
            text = await websocket.receive_text()
            
            # 生成完整音频
            wav_data = await tts.synthesize_full_audio(text)
            
            # 发送完整音频数据
            await websocket.send_bytes(wav_data)
            
    except WebSocketDisconnect:
        print("客户端断开连接")

# 前端代码 - 接收完整音频并播放
html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>TTS 完整音频播放</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h3 { color: #333; }
        textarea { width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 5px; border: 1px solid #ddd; }
        button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        #status { margin-top: 15px; color: #666; }
    </style>
</head>
<body>
    <h3>输入文本后点击播放，等待合成完成后一次性播放完整音频</h3>
    <textarea id="text" rows="4" cols="50">这是一个测试文本，现在系统会先生成完整的音频，然后再进行播放，这样可以避免流式播放时可能出现的杂音问题。</textarea><br/>
    <button id="btn">开始播放</button>
    <div id="status">准备就绪</div>

    <script>
        const btn = document.getElementById("btn");
        const textArea = document.getElementById("text");
        const status = document.getElementById("status");
        
        let audioCtx;
        let isProcessing = false;
        
        // 初始化音频上下文
        function initAudioContext() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            return audioCtx;
        }
        
        btn.onclick = async () => {
            const text = textArea.value.trim();
            if (!text) return alert("请输入文本！");
            
            if (isProcessing) return;
            isProcessing = true;
            status.textContent = "正在生成语音...";
            
            try {
                initAudioContext();
                
                // 创建WebSocket连接
                const ws = new WebSocket(`ws://${location.host}/ws/tts`);
                ws.binaryType = "arraybuffer";
                
                ws.onopen = () => {
                    status.textContent = "正在发送请求...";
                    ws.send(text);
                };
                
                ws.onmessage = async (event) => {
                    status.textContent = "处理音频数据...";
                    
                    try {
                        // 解码WAV数据
                        const audioBuffer = await audioCtx.decodeAudioData(event.data);
                        
                        // 播放音频
                        playAudioBuffer(audioBuffer);
                        status.textContent = "播放中...";
                        
                    } catch (error) {
                        console.error("解码音频失败:", error);
                        status.textContent = "播放失败: " + error.message;
                    }
                    
                    // 处理完成后关闭WebSocket
                    ws.close();
                    isProcessing = false;
                };
                
                ws.onclose = () => {
                    if (isProcessing) {
                        status.textContent = "已取消";
                        isProcessing = false;
                    }
                };
                
                ws.onerror = (e) => {
                    console.error("WebSocket错误:", e);
                    status.textContent = "发生错误";
                    isProcessing = false;
                };
                
            } catch (error) {
                console.error("生成语音失败:", error);
                status.textContent = "错误: " + error.message;
                isProcessing = false;
            }
        };
        
        function playAudioBuffer(audioBuffer) {
            const source = audioCtx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioCtx.destination);
            source.start();
            
            // 监听播放结束事件
            source.onended = () => {
                status.textContent = "播放完成";
            };
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)