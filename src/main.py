# 程序入口
import os

import dotenv
dotenv.load_dotenv()

from ui import create_demo
from base import PaddleOCRClient

async def parse_pdf(file):
    if not file:
        return "请先上传文件"
    
    file_path = file.name if hasattr(file, 'name') else file
    
    # 调用 OCR 解析，返回输出目录
    output_dir = await ocr.parse(file_path)
    
    # 读取生成的 doc.md 内容
    md_path = os.path.join(output_dir, "doc.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
            
    return "解析完成，但未找到 Markdown 文件。"

async def summarize_md(md_content):
    # TODO: 接入 LLM 总结逻辑
    return "暂未接入 LLM 总结功能"

if __name__ == "__main__":
    ocr = PaddleOCRClient()
    
    demo = create_demo(
        parse_func=parse_pdf,
        summarize_func=summarize_md
    )
    demo.launch()