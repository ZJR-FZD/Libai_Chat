from backend.speech.asr import ASR
from backend.speech.tts import TTSGenerator
from backend.dialog.dialog_manager import DialogManager
import time
import os
import asyncio

async def run_test():
    # 初始化组件
    print("初始化组件中...")
    start_time = time.perf_counter()
    
    asr = ASR()
    tts = TTSGenerator()
    dialog_manager = DialogManager()
    
    init_time = time.perf_counter() - start_time
    print(f"组件初始化完成，耗时: {init_time:.3f} 秒")
    
    # 读取音频文件
    audio_file_path = r'E:\李白语音智能体\audio_files\test16000_你是谁_是不是李白.wav'
    print(f"正在读取音频文件: {audio_file_path}")
    
    start_time = time.perf_counter()
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    read_time = time.perf_counter() - start_time
    print(f"音频文件读取完成，耗时: {read_time:.3f} 秒，文件大小: {len(audio_data)/1024:.2f} KB")
    
    # 语音识别
    print("开始语音识别...")
    start_time = time.perf_counter()
    
    input_text = asr.transcribe(audio_data)
    
    asr_time = time.perf_counter() - start_time
    print(f"语音识别完成，耗时: {asr_time:.3f} 秒")
    
    if input_text:
        print(f"识别结果: {input_text}")
    else:
        print("语音识别失败")
        return
    
    # 处理用户输入
    print("正在处理用户输入...")
    start_time = time.perf_counter()
    
    dialog_manager.add_user_message(input_text)
    
    add_msg_time = time.perf_counter() - start_time
    print(f"用户输入处理完成，耗时: {add_msg_time:.3f} 秒")
    
    # 生成回复
    print("生成AI回复中...")
    start_time = time.perf_counter()
    
    output_text = dialog_manager.generate_response()
    
    gen_resp_time = time.perf_counter() - start_time
    print(f"AI回复生成完成，耗时: {gen_resp_time:.3f} 秒")
    print(f"回复内容: {output_text}")
    
    # 语音合成
    print("开始语音合成...")
    start_time = time.perf_counter()
    
    # 确保这行在async函数内部
    audio_bytes = await tts.synthesize_full_audio(output_text)
    
    path = os.path.join(tts.audio_dir, "test_asr+llm+tts.wav")
    with open(path, "wb") as f:
        f.write(audio_bytes)
    print(f"✅ 成功保存 WAV 文件: {path}")
    
    tts_time = time.perf_counter() - start_time
    print(f"语音合成完成，耗时: {tts_time:.3f} 秒")
    
    # 打印总耗时
    total_time = init_time + read_time + asr_time + add_msg_time + gen_resp_time + tts_time
    print(f"\n===== 全流程处理完成，总耗时: {total_time:.3f} 秒 =====")
    print(f"各阶段耗时占比:")
    print(f"  - 初始化: {init_time/total_time*100:.1f}%")
    print(f"  - 文件读取: {read_time/total_time*100:.1f}%")
    print(f"  - 语音识别: {asr_time/total_time*100:.1f}%")
    print(f"  - 对话处理: {(add_msg_time+gen_resp_time)/total_time*100:.1f}%")
    print(f"  - 语音合成: {tts_time/total_time*100:.1f}%")

# 程序入口点
if __name__ == "__main__":
    # 使用asyncio.run运行顶级异步函数
    asyncio.run(run_test())