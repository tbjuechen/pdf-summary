"""消息系统"""
from typing import Optional, Dict, Any, Literal, Union, List
from datetime import datetime
from pydantic import BaseModel, Field

class ImageUrl(BaseModel):
    """图片链接详情"""
    url: str
    detail: Literal["auto", "low", "high"] = "auto"
    display_url: Optional[str] = None

class TextContent(BaseModel):
    """文本内容块"""
    type: Literal["text"] = "text"
    text: str

class ImageContent(BaseModel):
    """图片内容块"""
    type: Literal["image_url"] = "image_url"
    image_url: ImageUrl

# 定义内容项的联合类型
ContentItem = Union[TextContent, ImageContent]
MessageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):
    """消息类 - 强类型多模态支持"""
    
    role: MessageRole
    content: Union[str, List[ContentItem]] = Field(default="")
    
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # --- 工厂方法 (Factory Methods) ---
    
    @classmethod
    def user(cls, content: str = "") -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str = "") -> "Message":
        return cls(role="assistant", content=content)

    @classmethod
    def system(cls, content: str = "") -> "Message":
        return cls(role="system", content=content)

    # --- 操作方法 (Fluent Interface) ---

    def add_text(self, text: str) -> "Message":
        """追加文本 (支持链式调用)"""
        self._ensure_list_mode()
        # 此时 self.content 必定是 list，类型检查器可能需要显式提示，但在运行时是安全的
        if isinstance(self.content, list):
            self.content.append(TextContent(text=text))
        return self

    def add_image(
        self,
        url: str,
        detail: Literal["auto", "low", "high"] = "auto",
        display_url: Optional[str] = None,
    ) -> "Message":
        """追加图片 (支持链式调用)"""
        self._ensure_list_mode()
        if isinstance(self.content, list):
            self.content.append(
                ImageContent(image_url=ImageUrl(url=url, detail=detail, display_url=display_url))
            )
        return self

    def _ensure_list_mode(self):
        """将 content 统一转换为列表模式"""
        if isinstance(self.content, str):
            # 如果当前是字符串，且不为空，则转为 TextContent 对象；如果为空，则初始化空列表
            initial_items = [TextContent(text=self.content)] if self.content else []
            self.content = initial_items

    def to_openai_dict(self) -> Dict[str, Any]:
        """
        转换为 OpenAI API 兼容的字典
        利用 Pydantic V2 的 model_dump 自动处理递归序列化
        """
        return self.model_dump(
            mode='json', 
            include={'role', 'content'}, 
            exclude_none=True
        )

    def __str__(self) -> str:
        if isinstance(self.content, str):
            display_str = self.content
        else:
            parts = []
            for item in self.content:
                if isinstance(item, TextContent):
                    parts.append(item.text)
                elif isinstance(item, ImageContent):
                    raw_url = item.image_url.url
                    display_url = item.image_url.display_url or raw_url
                    if not (display_url.startswith("http://") or display_url.startswith("https://")):
                        if len(display_url) > 64:
                            display_url = display_url[:30] + "..." + display_url[-10:]
                    parts.append(f"[IMAGE: {display_url}]")
            display_str = "".join(parts) # 通常多模态内容是紧凑拼接的，或者用换行
        return f"[{self.role}] {display_str}"