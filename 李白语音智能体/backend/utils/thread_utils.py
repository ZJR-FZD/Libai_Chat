# utils/thread_utils.py
import asyncio
import threading
import queue
from typing import Callable, Optional, Any

class AsyncQueueProcessor:
    """异步队列处理器，用于在后台线程处理数据"""
    
    def __init__(self, processor: Callable, maxsize: int = 0):
        """
        初始化队列处理器
        
        Args:
            processor: 处理函数，将从队列中获取的数据作为参数
            maxsize: 队列最大长度，0表示无限制
        """
        self.queue = queue.Queue(maxsize=maxsize)
        self.processor = processor
        self.thread = None
        self.running = False
        
    def start(self, daemon: bool = True) -> None:
        """启动处理线程"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=daemon)
        self.thread.start()
        
    def stop(self, timeout: Optional[float] = None) -> None:
        """停止处理线程"""
        self.running = False
        self.queue.put(None)  # 发送停止信号
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout)
            
    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """向队列中添加数据"""
        self.queue.put(item, block=block, timeout=timeout)
        
    def _process_loop(self) -> None:
        """处理循环，在单独的线程中运行"""
        while self.running:
            try:
                item = self.queue.get(timeout=1)  # 1秒超时，允许检查运行状态
                
                if item is None:  # 停止信号
                    break
                    
                # 处理数据
                self.processor(item)
                
                self.queue.task_done()
            except queue.Empty:
                continue  # 队列为空，继续循环
            except Exception as e:
                print(f"队列处理错误: {e}")

class AsyncExecutor:
    """异步任务执行器，用于在asyncio事件循环中执行任务"""
    
    @staticmethod
    def run_coroutine_in_loop(coro, loop=None):
        """在指定的asyncio事件循环中运行协程"""
        if loop is None:
            loop = asyncio.get_event_loop()
            
        return asyncio.run_coroutine_threadsafe(coro, loop)