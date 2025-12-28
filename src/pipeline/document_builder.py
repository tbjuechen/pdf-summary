from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from loguru import logger

try:
    from ..utils import img2base64
    from .document import Document, ImageData
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from utils import img2base64
    from pipeline.document import Document, ImageData


class MarkdownDocumentBuilder:
    """将 OCR 生成的 doc.md 与图片整理为 Document 对象。"""

    _IMG_PATTERN = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"]", re.IGNORECASE)

    def __init__(self, output_root: Optional[str] = None) -> None:
        default_root = Path(__file__).resolve().parents[2] / "PDF_Extraction"
        self.output_root = Path(output_root) if output_root else default_root

    def build(self, pdf_name: str) -> Document:
        target_dir = self.output_root / pdf_name
        doc_path = target_dir / "doc.md"
        if not doc_path.exists():
            raise FileNotFoundError(f"doc.md not found for {pdf_name}: {doc_path}")

        content = doc_path.read_text(encoding="utf-8")
        images = self._gather_images(content, target_dir)

        document = Document(content=content, metadata={}, images=images)
        logger.info("[Builder] 已构建文档，包含图片数量 {}", len(images))
        return document

    def _gather_images(self, content: str, target_dir: Path) -> List[ImageData]:
        seen = set()
        images: List[ImageData] = []
        for match in self._IMG_PATTERN.finditer(content):
            relative_src = match.group(1)
            if relative_src in seen:
                continue
            seen.add(relative_src)

            image_path = (target_dir / relative_src).resolve()
            if not image_path.exists():
                logger.warning("[Builder] 图片未找到，跳过: {}", image_path)
                continue

            base64_data = img2base64(str(image_path))
            metadata = {"relative_path": relative_src}
            images.append(ImageData(data=base64_data, metadata=metadata, path=str(image_path)))

        return images


if __name__ == "__main__":
    sample_dir = Path(__file__).resolve().parents[2] / "PDF_Extraction"
    pdf_name = "PDF-example"

    builder = MarkdownDocumentBuilder(output_root=str(sample_dir))
    try:
        document = builder.build(pdf_name)
    except Exception as exc:
        logger.error("[Builder] 构建失败: {}", exc)
    else:
        logger.info("[Builder] 文本前 100 个字符:\n{}", document.content[:100])
        logger.info("[Builder] metadata: {}", document.metadata)
        logger.info("[Builder] doc_id: {}", document.doc_id)

        images = document.images or []
        logger.success("[Builder] 构建完成，图片数量: {}，全文长度: {}", len(images), len(document.content))

        for idx, image in enumerate(images, start=1):
            preview = image.data[:40] + "..." if len(image.data) > 40 else image.data
            logger.info(
                "[Builder] 图片 {} -> path: {}, data(Base64)预览: {}", idx, image.path, preview
            )
