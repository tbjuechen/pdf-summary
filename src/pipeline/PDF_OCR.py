import os
import asyncio
from dataclasses import dataclass, field
import sys
from typing import List, Dict, Optional
from pathlib import Path

# 获取当前文件的目录 (src/pipeline)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上一级目录 (src)
src_dir = os.path.dirname(current_dir)

# 将 src 目录添加到系统路径中，这样就能找到 base 模块了
if src_dir not in sys.path:
    sys.path.append(src_dir)
    
# 导入你提供的 PaddleOCR 客户端
from base.PaddleOCR import PaddleOCRClient
from loguru import logger

@dataclass
class ImageData:
    """图片元数据封装"""
    local_path: str
    filename: str
    # 后续步骤中可以添加 embedding 向量或云端 URL
    url: Optional[str] = None 

@dataclass
class ParsedDocument:
    """
    管道流转的核心数据对象。
    包含 OCR 后的原始数据，将在后续步骤中不断被丰富（清洗、切片）。
    """
    original_file_path: str
    markdown_content: str
    images: List[ImageData] = field(default_factory=list)
    output_dir: str = ""
    
    # 元数据
    metadata: Dict = field(default_factory=dict)

class PDFParser:
    """
    PDF Pipeline Step 1: 解析器
    职责：
    1. 调用 PaddleOCRClient 获取基础数据
    2. 读取生成的 Markdown 文件内容到内存
    3. 收集所有生成的图片路径
    4. 封装成 ParsedDocument 对象
    """
    
    def __init__(self, api_token: Optional[str] = None):
        # 初始化 PaddleOCR 客户端
        self.ocr_client = PaddleOCRClient(token=api_token)

    async def parse(self, file_path: str, output_base_dir: str = "output") -> ParsedDocument:
        """
        执行解析并返回结构化对象
        """
        file_path = str(Path(file_path).resolve())
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        logger.info(f"--- Pipeline Step 1: Parsing {os.path.basename(file_path)} ---")

        # 1. 调用 PaddleOCR 进行解析
        # PaddleOCR 会返回生成的文件列表 (包括 doc_0.md, doc_1.md 和 doc.md)
        generated_files = await self.ocr_client.parse(file_path, output_dir=output_base_dir)
        
        if not generated_files:
            raise RuntimeError("OCR parsing failed: No files generated.")

        # 2. 定位核心输出文件
        # PaddleOCR.py 逻辑：最后会生成合并后的 doc.md
        # 我们假设 output_dir 是基于文件名生成的子目录
        # 通过 generated_files 的第一个文件路径反推实际输出目录
        first_file = Path(generated_files[0])
        actual_output_dir = first_file.parent
        full_md_path = actual_output_dir / "doc.md"

        if not full_md_path.exists():
            # 如果没有 doc.md，尝试合并所有 doc_x.md (兜底策略)
            logger.warning("Merged doc.md not found, attempting to read individual pages.")
            content = self._merge_individual_mds(generated_files)
        else:
            with open(full_md_path, "r", encoding="utf-8") as f:
                content = f.read()

        # 3. 收集图片资源
        # PaddleOCR 将图片保存在同一目录下
        images = self._collect_images(actual_output_dir)

        # 4. 封装结果
        doc = ParsedDocument(
            original_file_path=file_path,
            markdown_content=content,
            images=images,
            output_dir=str(actual_output_dir),
            metadata={
                "parser": "PaddleOCR-v1",
                "raw_file_count": len(generated_files)
            }
        )

        logger.success(f"Parsing complete. Content length: {len(doc.markdown_content)}, Images found: {len(doc.images)}")
        return doc

    def _collect_images(self, directory: Path) -> List[ImageData]:
        """扫描输出目录下的所有图片文件"""
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        images = []
        for file in directory.iterdir():
            if file.suffix.lower() in image_extensions:
                images.append(ImageData(
                    local_path=str(file.absolute()),
                    filename=file.name
                ))
        return images

    def _merge_individual_mds(self, file_paths: List[str]) -> str:
        """读取所有分页 markdown 并合并"""
        contents = []
        # 简单的按文件名排序确保顺序，例如 doc_0.md, doc_1.md
        sorted_paths = sorted(
            [p for p in file_paths if os.path.basename(p).startswith("doc_") and p.endswith(".md")],
            key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
        )
        
        for p in sorted_paths:
            with open(p, "r", encoding="utf-8") as f:
                contents.append(f.read())
        return "\n\n".join(contents)

# --- 测试代码 ---
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    async def main():
        # 假设你配置了环境变量 PADDLE_OCR_TOKEN
        parser = PDFParser()
        
        # 替换为你实际的 PDF 路径
        test_pdf = "data/PDF-example.pdf" 
        
        try:
            # 获取解析后的对象
            doc = await parser.parse(test_pdf)
            
            print(f"\n=== 解析结果概览 ===")
            print(f"原文件: {doc.original_file_path}")
            print(f"输出目录: {doc.output_dir}")
            print(f"文本长度: {len(doc.markdown_content)} 字符")
            print(f"包含图片: {len(doc.images)} 张")
            print("文本前预览:\n" + "-"*20)
            print(doc.markdown_content[:200] + "...")
            
            # 这里得到的 doc 对象就可以直接传给 Pipeline 的下一个步骤了
            # 例如: enhancer.process(doc)
            
        except Exception as e:
            logger.error(f"Test failed: {e}")

    asyncio.run(main())