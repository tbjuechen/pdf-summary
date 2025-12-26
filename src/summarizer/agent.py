from ..pipeline import DocumentChunk, Document, ImageData
from ..base import LLMClient, Message

from typing import List

class Agent:
    def __init__(self, llm: LLMClient = None, system_prompt: str = ""):
        self._history: List[Message] = []
        self.llm = llm or LLMClient()
        self.system_prompt = system_prompt

    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self._history.append(message)
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()
    
    def get_history(self) -> list[Message]:
        """获取历史记录"""
        return self._history.copy()
    
    async def run(self, user_message: Message, **kwargs) -> str:
        """运行代理，返回模型回复"""
        all_messages = [Message.system(self.system_prompt)] + self._history + [user_message]
        response = await self.llm.achat(all_messages, **kwargs)
        return response.content
        