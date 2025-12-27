from ..pipeline import DocumentChunk, Document, ImageData
from ..base import LLMClient, Message

from typing import List
import asyncio

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
        self.add_message(user_message)
        self.add_message(response)
        return response.content
        

class DocumentSummarizationAgent(Agent):
    def __init__(self, llm: LLMClient = None):
        system_prompt = (
            "你是一个文档总结助手。"
            "请根据用户提供的文档内容，生成简洁明了的总结。"
        )
        super().__init__(llm, system_prompt)
    
    async def summarize_document(self, document: Document, **kwargs) -> str:
        """总结文档内容"""
        user_msg = Message.user(f"请总结以下文档内容：\n{document.content}")
        # 如果存在图片
        if document.images:
            [user_msg.add_image(img.data) for img in document.images]

        summary = await self.run(user_msg, **kwargs)
        return summary

    async def summarize_chunks(self, chunks: List[DocumentChunk], **kwargs) -> List[str]:
        """总结每个文档块的内容"""
        async def _summarize_single_chunk(chunk: DocumentChunk) -> str:
            user_msg = Message.user(f"请总结以下文档片段内容：\n{chunk.content}")
            if chunk.images:
                [user_msg.add_image(img.data) for img in chunk.images]
            
            # 不使用 self.run 以避免污染历史记录
            messages = [Message.system(self.system_prompt), user_msg]
            response = await self.llm.achat(messages, **kwargs)
            return response.content

        tasks = [_summarize_single_chunk(chunk) for chunk in chunks]
        return await asyncio.gather(*tasks)

    async def refine_summary(self, document_summary: str, chunk_summaries: List[str], **kwargs) -> str:
        """综合文档总结和块总结，生成最终总结"""
        chunks_text = ""
        for i, summary in enumerate(chunk_summaries):
            chunks_text += f"片段 {i+1} 总结：\n{summary}\n\n"
            
        prompt = (
            f"以下是文档的总体总结：\n{document_summary}\n\n"
            f"以下是文档各片段的详细总结：\n{chunks_text}"
            "请结合文档的总体总结和各片段的详细总结，生成一份最终的文档总结。\n"
            "要求：\n"
            "1. 补充总体总结中缺失的重要细节。\n"
            "2. 修正总体总结中可能存在的偏差。\n"
            "3. 保持总结的连贯性、条理性和准确性。\n"
            "4. 最终输出应该是一篇完整的总结文章。"
        )
        
        user_msg = Message.user(prompt)
        return await self.run(user_msg, **kwargs)
