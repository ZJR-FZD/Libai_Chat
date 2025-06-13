# backend/dialog/dialog_manager.py
from typing import List, Dict, Any
from backend.models.load_model import model
from backend.dialog.prompt_templates import SYSTEM_PROMPT
from backend.dialog.conversation_history import ConversationHistory

class DialogManager:
    def __init__(self):
        """初始化对话管理器"""
        self.system_prompt = SYSTEM_PROMPT
        self.conversation_history = ConversationHistory()
        
    def get_initial_messages(self) -> List[Dict[str, str]]:
        """获取初始对话消息（包含系统提示）"""
        return [{"role": "system", "content": self.system_prompt}]
    00
    def add_user_message(self, user_input: str) -> None:
        """添加用户消息到对话历史"""
        self.conversation_history.add_message("user", user_input)
    
    def generate_response(self, temperature: float = 0.7) -> str:
        """
        生成AI回复
        
        Args:
            temperature: 控制生成的随机性，值越高越随机
            
        Returns:
            AI生成的回复文本
        """
        # 获取完整对话历史（包括系统提示）
        messages = self.get_initial_messages() + self.conversation_history.get_history()
        
        # 调用模型生成回复
        response = model.generate_response(messages, temperature)
        
        # 将AI回复添加到对话历史
        self.conversation_history.add_message("assistant", response)
        
        return response
    
    def clear_conversation(self) -> None:
        """清空当前对话"""
        self.conversation_history.clear_history()

if __name__ == "__main__":
    # 测试DialogManager
    print("=== 李白智能体对话测试 ===")
    dialog_manager = DialogManager()
    
    # 添加初始用户消息
    dialog_manager.add_user_message("君乃何人？")
    
    # 生成回复
    response = dialog_manager.generate_response()
    print(f"李白: {response}")
    
    # 继续对话
    dialog_manager.add_user_message("欲往何处？")
    response = dialog_manager.generate_response()
    print(f"李白: {response}")
    
    # 显示对话历史
    print("\n=== 对话历史 ===")
    for message in dialog_manager.conversation_history.get_history():
        print(f"{message['role']}: {message['content']}")
    
    # 清空对话
    dialog_manager.clear_conversation()
    print("\n=== 清空对话后 ===")
    print("对话历史长度:", len(dialog_manager.conversation_history.get_history()))