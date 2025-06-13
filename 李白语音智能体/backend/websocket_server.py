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
        self.loop = asyncio.get_running_loop()
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
            text = self.asr.transcribe(bytes(self.audio_buffer), is_raw_pcm=True)
            self.audio_buffer.clear()

            if text:
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

    async def _synthesize_and_send(self, text: str, websocket):
        print(f"🧠 开始生成完整WAV语音并分段发送：{text}")
        try:
            wav_bytes = await self.tts.synthesize_full_audio(text)
            async for chunk in self._async_chunk_generator(wav_bytes):
                if self.user_speaking:
                    print("🔇 用户说话中，停止TTS发送")
                    break
                await websocket.send_bytes(chunk)
        except Exception as e:
            print(f"❗TTS发送失败: {e}")

    async def _async_chunk_generator(self, wav_bytes: bytes):
        for chunk in self.split_wav_bytes_into_chunks(wav_bytes):
            yield chunk
            await asyncio.sleep(0)  # 让出事件循环

    def split_wav_bytes_into_chunks(self, wav_bytes: bytes, chunk_size: int = 2048):
        """
        将完整 WAV 数据按块切分，每一块都是合法的 WAV 文件（包含头部 + 数据）。
        每个 chunk 可以独立被 decodeAudioData 解码。
        """
        if len(wav_bytes) < 44:
            raise ValueError("WAV 数据太短，缺失头部")

        header = wav_bytes[:44]
        data = wav_bytes[44:]

        for i in range(0, len(data), chunk_size):
            chunk_data = data[i:i + chunk_size]
            chunk_len = len(chunk_data)
            new_header = bytearray(header)
            new_header[4:8] = (chunk_len + 36).to_bytes(4, byteorder='little')
            new_header[40:44] = chunk_len.to_bytes(4, byteorder='little')
            yield bytes(new_header) + chunk_data

    def _interrupt_current_tts(self):
        if self.current_tts_task and not self.current_tts_task.done():
            self.current_tts_task.cancel()
            print("当前TTS任务已中断")

    def _pad_audio(self, audio: bytes, frame_size: int = 2) -> bytes:
        remainder = len(audio) % frame_size
        if remainder != 0:
            return audio + b'\x00' * (frame_size - remainder)
        return audio
