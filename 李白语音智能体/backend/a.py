import asyncio
import websockets
import sys
from backend.speech.asr import ASR
from backend.speech.tts import TTSGenerator
from backend.dialog.dialog_manager import DialogManager
from backend.utils.thread_utils import AsyncQueueProcessor, AsyncExecutor
from backend.speech.audio_processing import is_speaking, pcm_to_wav_bytes

class RealTimeWebSocketServer:
    def __init__(self):
        self.asr = ASR()
        self.tts = TTSGenerator()
        self.dialog_manager = DialogManager()
        self.clients = set()
        self.user_speaking = False
        self.current_tts_task = None
        self.audio_buffer = bytearray()
        self.loop = None
        
        # 确保Python能够正确输出中文
        if sys.stdout.encoding != 'utf-8':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    async def handle_connection(self, websocket, path):
        await websocket.accept()
        print("客户端已连接")
        self.clients.add(websocket)
        self.loop = asyncio.get_running_loop()  # 获取当前有效loop
        self.audio_processor = AsyncQueueProcessor(
            processor=lambda data: self._process_audio_chunk(data, websocket),
            maxsize=100
        )
        self.audio_processor.start()

        try:
            while True:
                audio_chunk = await websocket.receive_bytes()
                
                audio_chunk = self._pad_audio(audio_chunk)
                speaking = is_speaking(audio_chunk)

                if speaking and not self.user_speaking:
                    self._interrupt_current_tts()
                    self.user_speaking = True
                elif not speaking and self.user_speaking:
                    self.user_speaking = False

                self.audio_processor.put(audio_chunk)
        except websockets.exceptions.ConnectionClosedOK:
            print("客户端关闭连接")
        finally:
            self.clients.remove(websocket)
            self.audio_processor.stop()

    def _process_audio_chunk(self, audio_chunk: bytes, websocket):
        self.audio_buffer.extend(audio_chunk)

        if not self.user_speaking and len(self.audio_buffer) >= 32000:
            text = self.asr.transcribe(bytes(self.audio_buffer))
            self.audio_buffer.clear()

            if text:
                print(111)
                future = asyncio.run_coroutine_threadsafe(
                    self._handle_user_input(text, websocket),
                    self.loop
                )

                def callback(fut):
                    try:
                        fut.result()
                    except Exception as e:
                        print("❗_handle_user_input 执行失败:", e)

                future.add_done_callback(callback)

    async def _handle_user_input(self, text: str, websocket):
        print(f"识别到用户输入: {text}")
        self.dialog_manager.add_user_message(text)
        response_text = self.dialog_manager.generate_response()

        self.current_tts_task = asyncio.create_task(
            self._synthesize_and_send(response_text, websocket)
        )
        await self.current_tts_task

    # async def _synthesize_and_send(self, text: str, websocket):
    #     print(f"🧠 开始生成语音：{text}")
    #     try:
    #         async for chunk in self.tts.generate_pcm_chunks(text):
    #             print(f"📤 正在发送音频 chunk（{len(chunk)} 字节）")
    #             if self.user_speaking:
    #                 print("🔇 TTS播放中断")
    #                 break
    #             await websocket.send_bytes(chunk)
    #     except Exception as e:
    #         print(f"❗TTS发送失败: {e}")
    async def _synthesize_and_send(self, text: str, websocket):
        print(f"开始生成完整WAV语音：{text}")
        print(f"[播放前检测] self.user_speaking = {self.user_speaking}")

        try:
            if self.user_speaking:
                print("检测到用户讲话，中断TTS播放")
                return

            wav_bytes = await self.tts.synthesize_full_audio(text)

            if self.user_speaking:
                print("检测到用户讲话（合成后再次确认），中断TTS播放")
                return

            await websocket.send_bytes(wav_bytes)
            print(wav_bytes[:16])
            print(f"完整WAV音频发送完成，大小: {len(wav_bytes)} 字节")
        except Exception as e:
            print(f"TTS发送失败: {e}")

    def _interrupt_current_tts(self):
        if self.current_tts_task and not self.current_tts_task.done():
            self.current_tts_task.cancel()
            print("当前TTS任务已中断")

    def _pad_audio(self, audio: bytes, frame_size: int = 2) -> bytes:
        # 确保音频段长度是完整的格式尺寸
        remainder = len(audio) % frame_size
        if remainder != 0:
            return audio + b'\x00' * (frame_size - remainder)
        return audio



import asyncio
import websockets
import sys
import time
import traceback
from backend.speech.asr import ASR
from backend.speech.tts import TTSGenerator
from backend.dialog.dialog_manager import DialogManager
from backend.utils.thread_utils import AsyncQueueProcessor
from backend.speech.audio_processing import is_speaking


class RealTimeWebSocketServer:
    def __init__(self):
        self.asr = ASR()
        self.tts = TTSGenerator()
        self.dialog_manager = DialogManager()
        self.clients = set()
        self.user_speaking = False
        self.current_tts_task = None
        self.audio_buffer = bytearray()
        self.loop = None
        self.last_speaking_time = time.time()

        if sys.stdout.encoding != 'utf-8':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    async def handle_connection(self, websocket, path):
        await websocket.accept()
        print("客户端已连接")
        self.clients.add(websocket)
        self.loop = asyncio.get_running_loop()
        self.audio_processor = AsyncQueueProcessor(
            processor=lambda data: self._process_audio_chunk(data, websocket),
            maxsize=100
        )
        self.audio_processor.start()

        try:
            while True:
                audio_chunk = await websocket.receive_bytes()
                print(f"收到音频数据: {len(audio_chunk)} 字节, 首个字节: {audio_chunk[:1]}")

                audio_chunk = self._pad_audio(audio_chunk)
                speaking = is_speaking(audio_chunk)
                # print(f"[是否在说话] speaking={speaking}, 状态={self.user_speaking}")

                if speaking:
                    self.last_speaking_time = time.time()
                    if not self.user_speaking:
                       # print("[说话检测] 开始说话")
                        self._interrupt_current_tts()
                        self.user_speaking = True
                elif self.user_speaking and (time.time() - self.last_speaking_time > 0.8):
                    # print("[说话检测] 停止说话（静音超过1秒）")
                    self.user_speaking = False

                self.audio_processor.put(audio_chunk)

        except websockets.exceptions.ConnectionClosedOK:
            print("客户端关闭连接")
        finally:
            self.clients.remove(websocket)
            self.audio_processor.stop()

    def _process_audio_chunk(self, audio_chunk: bytes, websocket):
        try:
            self.audio_buffer.extend(audio_chunk)
            # print(f"[Buffer长度] 当前长度={len(self.audio_buffer)}")

            if not self.user_speaking and len(self.audio_buffer) >= 32000:
                print("[触发ASR] 开始识别")
                text = None
                try:
                    text = self.asr.transcribe(bytes(self.audio_buffer),is_raw_pcm=True)
                    print(f"[ASR结果] {text}")
                except Exception as e:
                    print("[ASR异常]", str(e))
                    traceback.print_exc()
                finally:
                    self.audio_buffer.clear()

                if text and text.strip():
                    print("[ASR] 开始调度 TTS 响应任务")
                    future = asyncio.run_coroutine_threadsafe(
                        self._handle_user_input(text.strip(), websocket),
                        self.loop
                    )
                    try:
                        result = future.result(timeout=10)
                        print("[调度] TTS任务完成")
                    except Exception as e:
                        print("[调度] TTS调度异常:", e)
        except Exception as e:
            print("[处理音频异常]", str(e))
            traceback.print_exc()

    async def _handle_user_input(self, text: str, websocket):
        print(f"识别到用户输入: {text}")
        self.dialog_manager.add_user_message(text)
        response_text = self.dialog_manager.generate_response()

        self.current_tts_task = asyncio.create_task(
            self._synthesize_and_send(response_text, websocket)
        )
        try:
            await self.current_tts_task
        except asyncio.CancelledError:
            print("TTS任务被取消")

    async def _synthesize_and_send(self, text: str, websocket):
        print(f"开始生成完整WAV语音：{text}")
        print(f"[播放前检测] self.user_speaking = {self.user_speaking}")

        try:
            if self.user_speaking:
                print("检测到用户讲话，中断TTS播放")
                return

            wav_bytes = await self.tts.synthesize_full_audio(text)

            if self.user_speaking:
                print("检测到用户讲话（合成后再次确认），中断TTS播放")
                return

            await websocket.send_bytes(wav_bytes)
            print(wav_bytes[:16])
            print(f"完整WAV音频发送完成，大小: {len(wav_bytes)} 字节")
        except Exception as e:
            print(f"TTS发送失败: {e}")
            traceback.print_exc()

    def _interrupt_current_tts(self):
        if self.current_tts_task and not self.current_tts_task.done():
            self.current_tts_task.cancel()
            print("当前TTS任务已中断")

    def _pad_audio(self, audio: bytes, frame_size: int = 2) -> bytes:
        remainder = len(audio) % frame_size
        if remainder != 0:
            return audio + b'\x00' * (frame_size - remainder)
        return audio
