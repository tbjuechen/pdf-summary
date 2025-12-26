from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from loguru import logger

try:
    from .document import Document
except ImportError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from pipeline.document import Document


class MarkdownReferenceCleaner:
    """移除 Markdown 文档中参考文献部分及其后内容。"""

    def __init__(self, headings: Iterable[str] | None = None) -> None:
        default_headers = ("references", "reference", "参考文献")
        self._headings = tuple(h.lower() for h in (headings or default_headers))
        self._pattern = re.compile(r"^\s{0,3}###?\s+(.+)$")

    def run(self, document: Document) -> Document:
        """返回删去参考文献部分后的 Document，并同步更新磁盘上的 doc.md。"""
        content = document.content
        cutoff = self._find_cutoff(content)
        if cutoff is None:
            logger.info("[Cleaner] 未检测到参考文献标题，保持原文不变")
            return document

        trimmed = content[:cutoff].rstrip() + "\n"
        document.content = trimmed
        self._write_back(document)
        logger.info("[Cleaner] 已移除参考文献及其后内容")
        return document

    def _find_cutoff(self, content: str) -> int | None:
        offset = 0
        for line in content.splitlines(keepends=True):
            match = self._pattern.match(line)
            if match and match.group(1).strip().lower() in self._headings:
                return offset
            offset += len(line)
        return None

    def _write_back(self, document: Document) -> None:
        output_dir = document.metadata.get("output_dir") if document.metadata else None
        if not output_dir:
            logger.warning("[Cleaner] 缺少 output_dir 元数据，跳过写回 doc.md")
            return

        doc_path = Path(output_dir) / "doc.md"
        if not doc_path.exists():
            logger.warning("[Cleaner] 未找到 doc.md，写回操作已跳过: {}", doc_path)
            return

        doc_path.write_text(document.content, encoding="utf-8")


if __name__ == "__main__":
    sample_dir = Path(__file__).resolve().parents[2] / "PDF_Extraction" / "PDF-example"
    doc_path = sample_dir / "doc.md"

    if not doc_path.exists():
        logger.warning("[Cleaner] 示例文档不存在，路径: {}", doc_path)
        raise SystemExit(0)

    document = Document(content=doc_path.read_text(encoding="utf-8"), metadata={"output_dir": str(sample_dir)})
    cleaner = MarkdownReferenceCleaner()
    cleaner.run(document)
    logger.success("[Cleaner] 示例文档处理完成，当前长度 {}", len(document.content))
