from backend.config import settings

class ConversationHistory:
    def __init__(self):
        """初始化对话历史"""
        self.history = []

    def add_message(self, role: str, content: str):
        """
        向对话历史中添加一条消息
        
        Args:
            role: 消息角色，如 "user" 或 "assistant"
            content: 消息内容
        """
        message = {"role": role, "content": content}
        self.history.append(message)
        # 保持对话历史长度不超过最大限制
        if len(self.history) > settings.MAX_HISTORY_LENGTH:
            self.history = self.history[-settings.MAX_HISTORY_LENGTH:]

    def get_history(self):
        """
        获取当前的对话历史
        
        Returns:
            对话历史列表
        """
        return self.history

    def clear_history(self):
        """
        清空对话历史
        """
        self.history = []


if __name__ == "__main__":
    # 测试 ConversationHistory 类
    history = ConversationHistory()

    # 添加消息
    history.add_message("user", "你好")
    history.add_message("assistant", "幸会")
    history.add_message("user", "今天天气如何？")

    # 获取对话历史
    current_history = history.get_history()
    print("当前对话历史:", current_history)

    # 清空对话历史
    history.clear_history()
    print("清空后对话历史:", history.get_history())