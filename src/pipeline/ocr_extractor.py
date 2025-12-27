from __future__ import annotations

import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from ..base.PaddleOCR import PaddleOCRClient
    from .document import Document
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from base.PaddleOCR import PaddleOCRClient
    from pipeline.document import Document


class PaddleOCROutputProcessor:
    ###调用 PaddleOCR解析PDF，仅保留 doc.md 与 imgs###
    
    """调用 PaddleOCR 并保留 doc.md 与 imgs 的简单封装。"""

    def __init__(
        self,
        client: Optional[PaddleOCRClient] = None,
        output_root: Optional[str] = None,
    ) -> None:
        self.client = client or PaddleOCRClient()
        default_root = Path(__file__).resolve().parents[2] / "PDF_Extraction"
        self.output_root = Path(output_root) if output_root else default_root
        self.output_root.mkdir(parents=True, exist_ok=True)

    async def run(self, pdf_path: str) -> Document:
        """执行 OCR，清理多余文件，并返回整理后的文档内容。"""
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF file not found: {source_path}")

        target_dir = self.output_root / source_path.stem
        logger.info("[Pipeline] PaddleOCR 开始处理 {}", source_path)

        await self.client.parse(str(source_path), output_dir=str(self.output_root))
        self._clean_outputs(target_dir)

        doc_path = target_dir / "doc.md"
        if not doc_path.exists():
            raise FileNotFoundError(f"doc.md not found: {doc_path}")

        metadata = {
            "source_pdf": str(source_path),
            "output_dir": str(target_dir),
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }

        logger.info("[Pipeline] PaddleOCR 处理完成，结果位于 {}", target_dir)
        return Document(content=doc_path.read_text(encoding="utf-8"), metadata=metadata)

    def _clean_outputs(self, target_dir: Path) -> None:
        """删除单页 Markdown、布局图和解析 JSON，仅保留 doc.md 与 imgs。"""
        if not target_dir.exists():
            return

        parsed_json = target_dir / "parsed_data_v2.json"
        if parsed_json.exists():
            parsed_json.unlink()

        for item in target_dir.iterdir():
            if item.name == "doc.md" or item.name == "imgs":
                continue
            if item.suffix == ".md" and item.name.startswith("doc_"):
                item.unlink()
                continue
            if item.suffix.lower() == ".json":
                item.unlink()
                continue
            if item.suffix.lower() in {".jpg", ".png"} and item.name.startswith("layout_det_res"):
                item.unlink()
                continue
            if item.is_dir() and item.name != "imgs":
                shutil.rmtree(item)
            elif item.is_file() and item.name != "doc.md":
                item.unlink()

    def run_sync(self, pdf_path: str) -> Document:
        """同步入口，方便在无事件循环环境中调用。"""
        return asyncio.run(self.run(pdf_path))


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    sample_pdf = Path("data/PDF-example.pdf")

    async def demo() -> None:
        processor = PaddleOCROutputProcessor()
        document = await processor.run(str(sample_pdf))
        logger.success("[Pipeline] 文档处理完成，长度 {}", len(document.content))

    if sample_pdf.exists():
        try:
            asyncio.run(demo())
        except Exception as exc:
            logger.error("[Pipeline] 处理失败: {}", exc)
    else:
        logger.warning("[Pipeline] 示例 PDF 不存在: {}", sample_pdf)
