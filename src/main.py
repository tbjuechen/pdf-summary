# 程序入口
import os
import time
import dotenv
import asyncio
dotenv.load_dotenv()

from ui import create_demo
from base import PaddleOCRClient

async def _parse_pdf_async(file):
    if not file:
        return "请先上传文件"
    
    start_time = time.time()
    file_path = file.name if hasattr(file, 'name') else file
    
    try:
        # 调用 OCR 解析，返回输出目录
        output_dir = await ocr.parse(file_path)
        
        # 读取生成的 doc.md 内容
        md_path = os.path.join(output_dir, "doc.md")
        content = ""
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "解析完成，但未找到 Markdown 文件。"
            
        elapsed = time.time() - start_time
        return f"> ⏱️ **解析耗时**: {elapsed:.2f} 秒\n\n{content}"
        
    except Exception as e:
        return f"❌ 解析出错: {str(e)}"

def parse_pdf_sync(file):
    return asyncio.run(_parse_pdf_async(file))

async def _summarize_md_async(md_content):
    start_time = time.time()
    
    # TODO: 接入 LLM 总结逻辑
    # 模拟异步耗时
    await asyncio.sleep(1)
    await asyncio.sleep(0.5)
    
    result = "暂未接入 LLM 总结功能"
    
    elapsed = time.time() - start_time
    return f"⏱️ 耗时: {elapsed:.2f}s\n\n{result}"

def summarize_md_sync(md_content):
    return asyncio.run(_summarize_md_async(md_content))

if __name__ == "__main__":
    ocr = PaddleOCRClient()
    
    demo = create_demo(
        parse_func=parse_pdf_sync,
        summarize_func=summarize_md_sync
    )
    demo.launch()