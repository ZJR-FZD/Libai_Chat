from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from backend.websocket_server import RealTimeWebSocketServer

app = FastAPI(title="李白语音智能体")

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>实时语音测试</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    h2 { color: #333; }
    button { padding: 10px 20px; margin: 5px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
    button:disabled { background-color: #cccccc; cursor: not-allowed; }
    #status { margin-top: 15px; color: #666; }
  </style>
</head>
<body>
  <h2>实时语音对话测试</h2>
  <button id="start">开始对话</button>
  <button id="stop" disabled>结束对话</button>
  <div id="status">准备就绪</div>

    <script>
    let ws;
    let audioContext;
    let mediaStream;
    let sourceNode;
    let isPlaying = false;
    let currentAudioBuffer = null;
    
    document.getElementById("start").onclick = async () => {
        document.getElementById("status").textContent = "正在连接...";
        
        // 创建WebSocket连接
        ws = new WebSocket("ws://localhost:8000/ws");
        ws.binaryType = 'arraybuffer';

        ws.onopen = () => {
            console.log("WebSocket 已连接");
            document.getElementById("status").textContent = "已连接，开始录音...";
        };
        
        ws.onmessage = async (e) => {
            if (e.data instanceof ArrayBuffer) {
                document.getElementById("status").textContent = "收到语音，正在解码...";
                
                try {
                    // 初始化AudioContext（如果尚未初始化）
                    if (!audioContext) {
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    }
                    
                    // 解码WAV音频数据
                    const audioBuffer = await audioContext.decodeAudioData(e.data);
                    
                    // 播放音频
                    playAudio(audioBuffer);
                    
                } catch (error) {
                    console.error("解码音频失败:", error);
                    document.getElementById("status").textContent = "播放失败: " + error.message;
                }
            }
        };

        ws.onclose = () => {
            console.log("WebSocket 已断开");
            document.getElementById("status").textContent = "连接已断开";
            document.getElementById("start").disabled = false;
            document.getElementById("stop").disabled = true;
        };

        ws.onerror = (error) => {
            console.error("WebSocket错误:", error);
            document.getElementById("status").textContent = "WebSocket错误";
        };

        try {
            // 获取麦克风音频
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            sourceNode = audioContext.createMediaStreamSource(mediaStream);
            
            // 创建ScriptProcessorNode处理音频
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            sourceNode.connect(processor);
            processor.connect(audioContext.destination);
            
            processor.onaudioprocess = (event) => {
                const inputBuffer = event.inputBuffer.getChannelData(0);
                
                // 将Float32转换为16位PCM
                const pcm16 = float32ToPCM16(inputBuffer);
                
                // 发送音频数据到服务器
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(pcm16);
                }
            };

            document.getElementById("start").disabled = true;
            document.getElementById("stop").disabled = false;
            
        } catch (error) {
            console.error("获取麦克风失败:", error);
            document.getElementById("status").textContent = "获取麦克风失败: " + error.message;
            if (ws) ws.close();
        }
    };

    document.getElementById("stop").onclick = () => {
        document.getElementById("status").textContent = "正在停止...";
        
        // 关闭所有连接和资源
        if (ws) {
            ws.close();
            ws = null;
        }
        
        if (sourceNode) {
            sourceNode.disconnect();
            sourceNode = null;
        }
        
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        
        if (audioContext && audioContext.state !== 'closed') {
            audioContext.close();
            audioContext = null;
        }
        
        isPlaying = false;
        currentAudioBuffer = null;
        
        document.getElementById("start").disabled = false;
        document.getElementById("stop").disabled = true;
        document.getElementById("status").textContent = "已停止";
    };

    function playAudio(audioBuffer) {
        document.getElementById("status").textContent = "正在播放...";
        currentAudioBuffer = audioBuffer;
        isPlaying = true;
        
        // 创建AudioBufferSourceNode播放音频
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        
        // 开始播放
        source.start();
        
        // 监听播放结束事件
        source.onended = () => {
            isPlaying = false;
            document.getElementById("status").textContent = "播放完成，等待输入...";
        };
    }

    function float32ToPCM16(float32Array) {
        const buffer = new ArrayBuffer(float32Array.length * 2);
        const view = new DataView(buffer);
        
        for (let i = 0; i < float32Array.length; i++) {
            const value = Math.max(-1, Math.min(1, float32Array[i]));
            view.setInt16(i * 2, value < 0 ? value * 0x8000 : value * 0x7FFF, true);
        }
        
        return new Uint8Array(buffer);
    }
    </script>

</body>
</html>
"""

server = RealTimeWebSocketServer()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await server.handle_connection(websocket, None)

@app.get("/")
async def get():
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)