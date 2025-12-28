# 程序入口
import os
import time
import dotenv
import asyncio
from typing import Any

dotenv.load_dotenv()

from ui import create_demo
from base import PaddleOCRClient
from pipeline import (
    MarkdownDocumentBuilder,
    MarkdownChunkBuilder,
    MarkdownReferenceCleaner,
    Document,
)
from summarizer.agent import DocumentSummarizationAgent

reference_cleaner = MarkdownReferenceCleaner()
chunk_builder = MarkdownChunkBuilder()
_latest_context: dict[str, Any] = {}
ocr: PaddleOCRClient | None = None
summarization_agent: DocumentSummarizationAgent | None = None

async def _parse_pdf_async(file):
    if not file:
        return "请先上传文件"
    
    start_time = time.time()
    file_path = file.name if hasattr(file, 'name') else file
    global _latest_context
    _latest_context = {}
    
    try:
        if ocr is None:
            return "❌ OCR 客户端未初始化"

        output_dir = await ocr.parse(file_path)
        abs_output_dir = os.path.abspath(output_dir)
        pdf_name = os.path.basename(abs_output_dir)
        output_root = os.path.dirname(abs_output_dir) or "."

        builder = MarkdownDocumentBuilder(output_root=output_root)
        document = builder.build(pdf_name)
        if document.metadata is None:
            document.metadata = {}
        document.metadata["output_dir"] = abs_output_dir

        cleaned_document = reference_cleaner.run(document)
        processed_document = Document(
            content=cleaned_document.content,
            metadata=dict(cleaned_document.metadata or {}),
            images=cleaned_document.images,
        )
        processed_document.metadata["output_dir"] = abs_output_dir

        chunks = chunk_builder.split(processed_document)

        _latest_context = {
            "output_dir": abs_output_dir,
            "document": processed_document,
            "chunks": chunks,
            "document_summary": None,
            "chunk_summaries": None,
            "final_summary": None,
        }

        content = processed_document.content or "解析完成，但文档内容为空。"
        elapsed = time.time() - start_time
        return f"> ⏱️ **解析耗时**: {elapsed:.2f} 秒\n\n{content}"
        
    except Exception as e:
        return f"❌ 解析出错: {str(e)}"

def parse_pdf_sync(file):
    return asyncio.run(_parse_pdf_async(file))

async def _summarize_md_async(md_content):
    start_time = time.time()
    if summarization_agent is None:
        return "❌ 总结代理未初始化"

    global _latest_context
    context = _latest_context or {}
    document = context.get("document")
    if document is None:
        return "请先完成解析，再生成总结"

    chunks = context.get("chunks") or []

    try:
        summarization_agent.clear_history()
        document_summary = await summarization_agent.summarize_document(document)

        chunk_summaries: list[str] = []
        if chunks:
            summarization_agent.clear_history()
            chunk_summaries = await summarization_agent.summarize_chunks(chunks)

        final_summary = document_summary
        if chunk_summaries:
            summarization_agent.clear_history()
            final_summary = await summarization_agent.refine_summary(document_summary, chunk_summaries)

        summarization_agent.clear_history()

        elapsed = time.time() - start_time

        updated_context = dict(context)
        updated_context["document_summary"] = document_summary
        updated_context["chunk_summaries"] = chunk_summaries
        updated_context["final_summary"] = final_summary
        _latest_context = updated_context

        sections: list[str] = [
            f"> ⏱️ **总结耗时**: {elapsed:.2f} 秒",
            "## 最终总结",
            final_summary,
        ]

        if chunk_summaries:
            sections.append("## 片段总结")
            for index, chunk_summary in enumerate(chunk_summaries, start=1):
                sections.append(f"### 片段 {index}\n{chunk_summary}")

        return "\n\n".join(sections)

    except Exception as exc:
        return f"❌ 总结出错: {str(exc)}"

def summarize_md_sync(md_content):
    return asyncio.run(_summarize_md_async(md_content))

if __name__ == "__main__":
    ocr = PaddleOCRClient()
    summarization_agent = DocumentSummarizationAgent()
    
    demo = create_demo(
        parse_func=parse_pdf_sync,
        summarize_func=summarize_md_sync
    )
    demo.launch()