# backend/models/load_model.py
import os
import requests
import json
from typing import List, Dict, Any
from backend.config import settings

class QwenModel:
    def __init__(self):
        """初始化Qwen模型API客户端"""
        self.api_base_url = settings.QWEN_API_URL
        self.api_key = settings.QWEN_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        调用Qwen API生成回复
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, {"role": "assistant", "content": "幸会"}]
            temperature: 控制生成的随机性，值越高越随机
        
        Returns:
            模型生成的回复文本
        """
        try:
            payload = {
                "model": settings.QWEN_MODEL_NAME,  
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2048,
                "stream": False
            }
            
            response = requests.post(
                self.api_base_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("choices", [{}])[0].get("message", {}).get("content", "回复为空")
            
        except Exception as e:
            print(f"Error: {e}")
            print(f"Response: {response.content.decode('utf-8')}")
            return "抱歉，方才思绪有些飘远，未能听清你的问题。"

# 单例模式初始化模型
model = QwenModel()

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "你是唐代诗人李白，以诗酒为伴，豪放不羁。"},
        {"role": "user", "content": "阁下何人？为何在此独酌？"}
    ] 
    reply = model.generate_response(messages)
    print("李白回复:", reply)