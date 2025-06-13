import io
import torch
import whisper
import numpy as np
import ffmpeg
from typing import Optional
from backend.config import settings

class ASR:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(settings.ASR_MODEL, device=self.device)

    def transcribe(self, audio_data: bytes, is_raw_pcm: bool = False) -> Optional[str]:
        try:
            input_kwargs = {'format': 's16le', 'ac': 1, 'ar': '16000'} if is_raw_pcm else {}
            out, _ = (
                ffmpeg
                .input('pipe:0', **input_kwargs)
                .output('pipe:1', format='f32le', ac=1, ar='16000')
                .run(input=audio_data, capture_stdout=True, capture_stderr=True)
            )
            audio = np.frombuffer(out, np.float32)
            result = self.model.transcribe(audio, fp16=torch.cuda.is_available())
            return result["text"].strip()
        except Exception as e:
            print(f"ASR错误: {e}")
            return None

if __name__ == "__main__":
    audio_file_path = r'E:\李白语音智能体\audio_files\test16000_你是谁_是不是李白.wav'
    
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()

    asr = ASR()
    text = asr.transcribe(audio_data,False)
    if text:
        print(f"识别结果: {text}")
    else:
        print("语音识别失败")