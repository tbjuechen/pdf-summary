import gradio as gr
import os
import time

from gradio_pdf import PDF

# ==========================================
# 1. 核心处理逻辑 (模拟解析和总结)
# ==========================================
def mock_parse(file_obj):
    if file_obj is None:
        return "请先上传文件"
    
    # 兼容性处理
    if hasattr(file_obj, 'name'):
        file_path = file_obj.name
    else:
        file_path = file_obj

    filename = os.path.basename(file_path)
    
    print(f"正在解析文件: {filename}...")
    time.sleep(1) 
    
    return f"""# {filename} 解析结果\n\n**文件名**: {filename}\n**文件大小**: {os.path.getsize(file_path)/1024:.1f} KB\n\n这里是模拟的解析内容..."""

def mock_summarize(md_content):
    if not md_content:
        return "无内容"
        
    print("正在生成总结...")
    time.sleep(1)
    return f"【AI 总结】\n这是一份关于该文档的总结...\n\n基于内容片段：{md_content[:20]}..."

# ==========================================
# 2. 预览逻辑
# ==========================================
def display_pdf(file_obj):
    if file_obj is None:
        return None
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

# ==========================================
# 3. 前端布局工厂函数
# ==========================================
def create_demo(parse_func, summarize_func):
    with gr.Blocks(title="PDF 解析助手", theme="soft") as demo:
        gr.Markdown("## 📄 智能文档解析系统")
        
        with gr.Row():
            # --- 左侧：上传与预览 ---
            with gr.Column(scale=5):
                file_input = gr.File(label="上传 PDF", file_types=[".pdf"])
                run_btn = gr.Button("🚀 开始解析", variant="primary")
                
                # 【核心修改】没有 gr.PDF，所以我们用 gr.HTML
                pdf_preview = PDF(label="文档预览", height=600)

            # --- 右侧：结果输出 ---
            with gr.Column(scale=5):
                with gr.Accordion("Markdown 解析结果", open=True):
                    # 使用 Textbox 可以更方便地复制内容，也能看到原始 Markdown 语法
                    md_output = gr.Textbox(label="Markdown 内容", lines=20)
                
                # 新增：单独的总结按钮（可选）
                with gr.Row():
                    summ_btn = gr.Button("🧠 生成/重新总结", size="sm")
                
                summary_output = gr.Textbox(label="AI 总结", lines=8)

        # ==========================================
        # 4. 交互逻辑
        # ==========================================
        
        # 上传文件后 -> 更新预览
        file_input.change(fn=display_pdf, inputs=file_input, outputs=pdf_preview)
        
        # 点击“开始解析” -> 先解析 -> 再总结 (链式调用)
        run_btn.click(fn=parse_func, inputs=file_input, outputs=md_output) \
               .then(fn=summarize_func, inputs=md_output, outputs=summary_output)
        
        # 点击“生成总结” -> 仅执行总结 (允许用户修改 Markdown 后重新总结)
        summ_btn.click(fn=summarize_func, inputs=md_output, outputs=summary_output)
    
    return demo

# 创建默认 demo 实例 (使用 mock 逻辑)
demo = create_demo(mock_parse, mock_summarize)

if __name__ == "__main__":
    demo.launch()