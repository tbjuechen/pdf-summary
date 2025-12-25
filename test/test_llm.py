import pytest
import os
import sys

from unittest.mock import MagicMock, patch, AsyncMock
from base.llm import LLMClient
from base.message import Message

class TestLLMClient:
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock 环境变量"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo-test")
        monkeypatch.setenv("OPENAI_API_BASE", "https://api.test.com/v1")

    @pytest.fixture
    def llm_client(self, mock_env):
        """创建一个 LLMClient 实例"""
        return LLMClient()

    def test_init_defaults(self, mock_env):
        """测试默认初始化"""
        client = LLMClient()
        assert client.api_key == "sk-test-key"
        assert client.model == "gpt-3.5-turbo-test"
        assert client.base_url == "https://api.test.com/v1"
        assert client.temperature == 0.7

    def test_init_custom(self):
        """测试自定义参数初始化"""
        client = LLMClient(
            api_key="sk-custom",
            model="gpt-4",
            base_url="https://custom.api/v1",
            temperature=0.5,
            max_tokens=100
        )
        assert client.api_key == "sk-custom"
        assert client.model == "gpt-4"
        assert client.base_url == "https://custom.api/v1"
        assert client.temperature == 0.5
        assert client.max_tokens == 100

    def test_init_missing_key(self, monkeypatch):
        """测试缺少 API Key 时抛出异常"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="必须提供 api_key"):
            LLMClient()

    def test_normalize_messages_with_objects(self, llm_client):
        """测试 Message 对象列表的标准化"""
        msgs = [Message.user("hello"), Message.assistant("hi")]
        normalized = llm_client._normalize_messages(msgs)
        
        assert len(normalized) == 2
        assert normalized[0] == {"role": "user", "content": "hello"}
        assert normalized[1] == {"role": "assistant", "content": "hi"}

    def test_normalize_messages_with_dicts(self, llm_client):
        """测试字典列表的标准化"""
        msgs = [{"role": "user", "content": "hello"}]
        normalized = llm_client._normalize_messages(msgs)
        assert normalized == msgs

    def test_build_request_params(self, llm_client):
        """测试请求参数构建"""
        msgs = [Message.user("test")]
        params = llm_client._build_request_params(msgs, stream=True)
        
        assert params["model"] == "gpt-3.5-turbo-test"
        assert params["temperature"] == 0.7
        assert params["messages"][0]["content"] == "test"
        assert params["stream"] is True

    @patch("base.llm.OpenAI")
    def test_chat_sync(self, mock_openai_cls, llm_client):
        """测试同步聊天"""
        # Mock 响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
        
        # 设置 Mock 客户端
        mock_client_instance = mock_openai_cls.return_value
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        # 触发 lazy load
        _ = llm_client.sync_client
        
        response = llm_client.chat([Message.user("Hi")])
        
        assert response.content == "Hello world"
        mock_client_instance.chat.completions.create.assert_called_once()
        
        # 验证调用参数
        call_kwargs = mock_client_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-3.5-turbo-test"
        assert call_kwargs["messages"][0]["content"] == "Hi"

    def test_chat_async(self, llm_client):
        """测试异步聊天"""
        import asyncio
        
        async def run_test():
            with patch("base.llm.AsyncOpenAI") as mock_async_cls:
                # Mock 响应
                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content="Async Hello"))]
                
                # 设置 Mock 客户端
                mock_client_instance = mock_async_cls.return_value
                mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
                
                # 触发 lazy load
                _ = llm_client.async_client
                
                response = await llm_client.achat([Message.user("Hi")])
                
                assert response.content == "Async Hello"
                mock_client_instance.chat.completions.create.assert_called_once()

        asyncio.run(run_test())

    @patch("base.llm.OpenAI")
    def test_simple_chat_with_image(self, mock_openai_cls, llm_client):
        """测试带图片的简单聊天"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Image description"))]
        
        mock_client_instance = mock_openai_cls.return_value
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        _ = llm_client.sync_client
        
        response = llm_client.simple_chat(
            system_prompt="You are a vision model",
            user_message="Describe this",
            image_url="https://example.com/img.png"
        )
        
        assert response.content == "Image description"
        
        # 验证消息结构
        call_kwargs = mock_client_instance.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        
        user_msg = messages[1]
        assert user_msg["role"] == "user"
        assert isinstance(user_msg["content"], list)
        # 检查是否包含文本和图片
        has_text = any(item.get("type") == "text" and item.get("text") == "Describe this" for item in user_msg["content"])
        has_image = any(item.get("type") == "image_url" and item["image_url"]["url"] == "https://example.com/img.png" for item in user_msg["content"])
        
        assert has_text
        assert has_image
