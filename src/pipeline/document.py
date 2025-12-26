from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class ImageData:
    """图片数据类"""
    data: bytes
    metadata: Dict[str, Any]
    path: str

@dataclass
class Document:
    """文档类"""
    content: str
    metadata: Dict[str, Any]
    doc_id: Optional[str] = None
    images: List[ImageData] = None

    def __post_init__(self):
        if self.doc_id is None:
            self.doc_id = hashlib.md5(self.content.encode()).hexdigest()

@dataclass
class DocumentChunk:
    """文档块类"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    doc_id: Optional[str] = None
    chunk_index: int = 0
    images: List[ImageData] = None

    def __post_init__(self):
        if self.chunk_id is None:
            chunk_content = f"{self.doc_id}_{self.chunk_index}_{self.content[:50]}"
            self.chunk_id = hashlib.md5(chunk_content.encode()).hexdigest()
