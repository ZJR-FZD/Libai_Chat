import io
import wave
from pydub import AudioSegment
from pydub.silence import split_on_silence
from typing import Optional
from pydub.utils import mediainfo

def is_speaking(audio_chunk: bytes, silence_thresh: int = -40, sample_rate=16000, channels=1) -> bool:
    """
    判断音频 chunk 中是否有明显讲话信号（非静音）。
    
    Args:
        audio_chunk: 一段裸 PCM 音频数据 bytes
        silence_thresh: 静音阈值，单位 dBFS，默认 -40dBFS
        sample_rate: 采样率，默认16000 Hz
        channels: 声道数，默认单声道
    
    Returns:
        bool: 是否为“正在说话”
    """
    try:
        audio = AudioSegment.from_raw(
            io.BytesIO(audio_chunk),
            sample_width=2,  # 16-bit PCM = 2 bytes
            frame_rate=sample_rate,
            channels=channels
        )
        return audio.dBFS > silence_thresh
    except Exception as e:
        print(f"判断是否说话时出错: {e}")
        return False

def pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate=16000, channels=1, sampwidth=2) -> bytes:
    """
    把裸 PCM 数据封装成 WAV 格式字节流
    sampwidth: 每个采样字节数，2表示16bit
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buf.getvalue()

def wav_to_pcm_bytes(wav_path: str) -> bytes:
    with wave.open(wav_path, 'rb') as wav_file:
        # 检查基本信息（可选）
        # print("声道数:", wav_file.getnchannels())
        # print("采样率:", wav_file.getframerate())
        # print("采样宽度:", wav_file.getsampwidth())
        # print("帧数:", wav_file.getnframes())
        
        pcm_bytes = wav_file.readframes(wav_file.getnframes())
    return pcm_bytes

def convert_audio_format(audio_file_path: str, source_format: str, target_format: str) -> Optional[bytes]:
    """
    转换音频格式
    
    Args:
        audio_file_path: 音频文件路径
        source_format: 源格式（如 'wav'）
        target_format: 目标格式（如 'mp3'）
        
    Returns:
        转换后的音频数据字节流，失败时返回None
    """
    try:
        audio = AudioSegment.from_file(audio_file_path, format=source_format)
        output = io.BytesIO()
        audio.export(output, format=target_format)
        return output.getvalue()
    except Exception as e:
        print(f"音频格式转换错误: {e}")
        return None

def adjust_audio_volume(audio_file_path: str, volume_change: float) -> Optional[bytes]:
    """
    调整音频音量
    
    Args:
        audio_file_path: 音频文件路径
        volume_change: 音量变化值（dB）
        
    Returns:
        调整后的音频数据字节流，失败返回None
    """
    try:
        audio = AudioSegment.from_file(audio_file_path)
        audio = audio + volume_change
        output = io.BytesIO()
        audio.export(output, format="wav")
        return output.getvalue()
    except Exception as e:
        print(f"音频音量调整错误: {e}")
        return None

def merge_audio_files(audio_file_path1: str, audio_file_path2: str) -> Optional[bytes]:
    """
    合并两个音频文件
    
    Args:
        audio_file_path1: 第一个音频文件路径
        audio_file_path2: 第二个音频文件路径
        
    Returns:
        合并后的音频数据字节流，失败返回None
    """
    try:
        audio1 = AudioSegment.from_file(audio_file_path1)
        audio2 = AudioSegment.from_file(audio_file_path2)
        
        # 统一音频长度
        if len(audio1) > len(audio2):
            audio2 = audio2 + AudioSegment.silent(duration=len(audio1) - len(audio2))
        else:
            audio1 = audio1 + AudioSegment.silent(duration=len(audio2) - len(audio1))
            
        merged = audio1.overlay(audio2)
        output = io.BytesIO()
        merged.export(output, format="wav")
        return output.getvalue()
    except Exception as e:
        print(f"音频合并错误: {e}")
        return None

def get_audio_duration(audio_file_path: str) -> float:
    """
    获取音频时长（秒）
    
    Args:
        audio_file_path: 音频文件路径
        
    Returns:
        音频时长（秒）
    """
    with wave.open(audio_file_path, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
        return duration

def split_audio_on_silence(audio_file_path: str, min_silence_len: int = 500, silence_thresh: int = -40) -> list:
    """
    根据静音分割音频
    
    Args:
        audio_file_path: 音频文件路径
        min_silence_len: 最小静音长度，单位毫秒
        silence_thresh: 静音阈值，单位dBFS
        
    Returns:
        分割后的音频片段字节流列表
    """
    try:
        audio = AudioSegment.from_file(audio_file_path)
        segments = split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=500
        )
        # 导出每段为bytes
        return [segment.export(io.BytesIO(), format="wav").getvalue() for segment in segments]
    except Exception as e:
        print(f"分割音频错误: {e}")
        return []

if __name__=="__main__":
    audio_file_path = r'E:\李白语音智能体\backend\人声-中文-你好(你好)_爱给网_aigei_com.wav'

    # 转换格式测试
    converted_data = convert_audio_format(audio_file_path, 'wav', 'mp3')
    print("音频格式转换成功" if converted_data else "音频格式转换失败")

    # 调整音量测试
    adjusted_data = adjust_audio_volume(audio_file_path, 5.0)
    print("音频音量调整成功" if adjusted_data else "音频音量调整失败")

    # 合并音频测试
    merged_data = merge_audio_files(audio_file_path, audio_file_path)
    print("音频合并成功" if merged_data else "音频合并失败")

    # 获取时长测试
    try:
        duration = get_audio_duration(audio_file_path)
        print(f"音频时长: {duration} 秒")
    except Exception as e:
        print(f"获取音频时长时出错: {e}")

    # 静音分割测试
    segments = split_audio_on_silence(audio_file_path)
    print("分割音频成功" if segments else "分割音频失败")
