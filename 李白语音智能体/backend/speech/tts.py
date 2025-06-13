import os
import asyncio
import edge_tts
from typing import AsyncGenerator
from backend.utils.file_utils import clean_directory
from backend.speech.audio_processing import pcm_to_wav_bytes
from backend.config import settings
import io
import wave

class TTSGenerator:
    def __init__(self):
        self.voice = "zh-CN-YunjianNeural"
        self.rate = "+0%"
        self.sample_rate = 16000  # 固定采样率为16000Hz
        self.audio_dir = settings.AUDIO_DIR
        clean_directory(self.audio_dir)

    async def synthesize_full_audio(self, text: str) -> bytes:
        """生成完整的WAV格式音频"""
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        stream = communicate.stream()

        pcm_data = bytearray()
        async for chunk in stream:
            if chunk["type"] == "audio":
                pcm_data.extend(chunk["data"])
        
        # 将PCM数据封装为WAV格式
        return pcm_to_wav_bytes(pcm_data)
    
    async def generate_pcm_chunks_async(self, text: str) -> AsyncGenerator[bytes, None]:
        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            stream = communicate.stream()

            raw_audio = bytearray()
            async for chunk in stream:
                if chunk["type"] == "audio":
                    raw_audio.extend(chunk["data"])

            # 裸PCM数据，直接封装成WAV
            wav_bytes = pcm_to_wav_bytes(bytes(raw_audio))

            # 从wav_bytes中用 wave 读取 PCM 分块返回
            wav_buffer = io.BytesIO(wav_bytes)
            with wave.open(wav_buffer, "rb") as wav_file:
                if wav_file.getsampwidth() != 2 or wav_file.getnchannels() != 1:
                    raise ValueError("仅支持16bit单声道音频")

                frame_size = 3200
                while True:
                    pcm_chunk = wav_file.readframes(frame_size // 2)
                    if not pcm_chunk:
                        break
                    yield pcm_chunk
        except Exception as e:
            print(f"TTS错误: {e}")


    def generate_pcm_chunks(self, text: str) -> AsyncGenerator[bytes, None]:
        return self.generate_pcm_chunks_async(text)

# 测试函数（保存为本地 WAV 文件）
async def test_wav_save():
    tts = TTSGenerator()
    text = "你是谁，是不是李白？"
    wav_bytes = await tts.synthesize_full_audio(text)
    path = os.path.join(tts.audio_dir, "test16000_你是谁_是不是李白.wav")
    with open(path, "wb") as f:
        f.write(wav_bytes)
    print(f"✅ 成功保存 WAV 文件: {path}")

if __name__ == "__main__":
    asyncio.run(test_wav_save())
