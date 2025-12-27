from __future__ import annotations

import re
from pathlib import Path
from typing import List

from loguru import logger

try:
    from ..utils import img2base64
    from .document_builder import MarkdownDocumentBuilder
    from .document import Document, DocumentChunk, ImageData
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from utils import img2base64
    from pipeline.document_builder import MarkdownDocumentBuilder
    from pipeline.document import Document, DocumentChunk, ImageData


class MarkdownChunkBuilder:
    """根据标题拆分 Markdown 文本并生成 DocumentChunk 列表。"""

    _HEADING_PATTERN = re.compile(
        r"(?m)^\s{0,3}###?\s+(\d+)(?:\.(?!\d))?(?=\s)",
    )
    _IMG_PATTERN = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"]", re.IGNORECASE)

    def split(self, document: Document) -> List[DocumentChunk]:
        """按规则切片 Document，并返回 DocumentChunk 列表。"""
        content = document.content
        if not content.strip():
            logger.warning("[Chunker] 文档内容为空，跳过切片")
            return []

        matches = list(self._HEADING_PATTERN.finditer(content))
        chunks: List[DocumentChunk] = []
        image_abs_map = {
            Path(img.path).resolve(): img for img in (document.images or []) if img.path
        }
        image_rel_map = {
            img.metadata.get("relative_path"): img
            for img in (document.images or [])
            if img.metadata.get("relative_path")
        }

        def add_chunk(text: str) -> None:
            normalized = text.strip()
            if not normalized:
                return
            chunk = DocumentChunk(
                content=normalized,
                metadata={},
                doc_id=document.doc_id,
                chunk_index=len(chunks),
                images=self._collect_images(normalized, image_abs_map, image_rel_map),
            )
            chunks.append(chunk)

        if not matches:
            add_chunk(content)
            logger.info("[Chunker] 未匹配到切片标题，返回整体文档作为单块")
            return chunks

        first_start = matches[0].start()
        if first_start > 0:
            add_chunk(content[:first_start])

        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            add_chunk(content[start:end])

        logger.info("[Chunker] 切片完成，共生成 {} 个文档块", len(chunks))
        return chunks

    def _collect_images(
        self,
        chunk_content: str,
        image_abs_map: dict[Path, ImageData],
        image_rel_map: dict[str, ImageData],
    ) -> List[ImageData]:
        """根据 chunk 内引用的图片路径收集图像。"""
        result: List[ImageData] = []
        if not chunk_content:
            return result

        relative_paths = {
            path.strip()
            for path in self._IMG_PATTERN.findall(chunk_content)
            if path.strip()
        }

        for rel_path in relative_paths:
            image = self._resolve_image(rel_path, image_abs_map, image_rel_map)
            if image:
                result.append(
                    ImageData(data=image.data, metadata=dict(image.metadata or {}), path=image.path)
                )

        return result

    def _resolve_image(
        self,
        rel_path: str,
        image_abs_map: dict[Path, ImageData],
        image_rel_map: dict[str, ImageData],
    ) -> ImageData | None:
        if rel_path in image_rel_map:
            return image_rel_map[rel_path]

        abs_candidates = [Path(rel_path).resolve()]
        abs_candidates.extend(
            path for path in image_abs_map.keys() if path.name == Path(rel_path).name
        )

        for abs_path in abs_candidates:
            if abs_path in image_abs_map:
                return image_abs_map[abs_path]

        candidate_path = Path(rel_path)
        if candidate_path.exists():
            base64_data = img2base64(str(candidate_path))
            metadata = {"relative_path": candidate_path.name}
            return ImageData(data=base64_data, metadata=metadata, path=str(candidate_path))

        return None


if __name__ == "__main__":
    sample_root = Path(__file__).resolve().parents[2] / "PDF_Extraction"
    pdf_name = "PDF-example"

    builder = MarkdownDocumentBuilder(output_root=str(sample_root))
    try:
        document = builder.build(pdf_name)
    except Exception as exc:
        logger.error("[Chunker] 构建 Document 失败: {}", exc)
        raise SystemExit(1)

    chunker = MarkdownChunkBuilder()
    chunks = chunker.split(document)

    logger.success("[Chunker] 生成 {} 个 chunk", len(chunks))
    for chunk in chunks:
        preview = chunk.content[:80].replace("\n", " ")
        image_paths = [image.path for image in chunk.images or []]
        logger.info(
            "[Chunker] chunk_index={}, chunk_id={}, doc_id={}, 长度={}, 预览={}",
            chunk.chunk_index,
            chunk.chunk_id,
            chunk.doc_id,
            len(chunk.content),
            preview,
        )
        logger.info("[Chunker] 图片列表: {}", image_paths)
