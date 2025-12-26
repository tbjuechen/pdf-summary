import gradio as gr
import os
import time

from gradio_pdf import PDF

# ==========================================
# 1. 核心处理逻辑 (模拟解析和总结)
# ==========================================
def main_process(file_obj):
    if file_obj is None:
        return "请先上传文件", "无内容"
    
    # 兼容性处理：不同版本的 Gradio，file_obj 可能是路径字符串，也可能是对象
    if hasattr(file_obj, 'name'):
        file_path = file_obj.name
    else:
        file_path = file_obj

    filename = os.path.basename(file_path)
    
    # --- 模拟耗时操作 ---
    print(f"正在处理文件: {filename}...")
    time.sleep(1) 
    
    md_result = f"""# {filename} 解析结果\n\n**文件名**: {filename}\n**文件大小**: {os.path.getsize(file_path)/1024:.1f} KB\n\n这里是模拟的解析内容..."""
    summary_result = f"【AI 总结】\n这是一份关于 {filename} 的文档..."
    
    return md_result, summary_result

# ==========================================
# 2. 预览逻辑
# ==========================================
def display_pdf(file_obj):
    if file_obj is None:
        return None
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

# ==========================================
# 3. 前端布局
# ==========================================
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
                md_output = gr.Markdown()
            summary_output = gr.Textbox(label="AI 总结", lines=8)

    # ==========================================
    # 4. 交互逻辑
    # ==========================================
    
    # 上传文件后 -> 更新预览
    file_input.change(fn=display_pdf, inputs=file_input, outputs=pdf_preview)
    
    # 点击按钮 -> 执行业务逻辑
    run_btn.click(fn=main_process, inputs=file_input, outputs=[md_output, summary_output])

if __name__ == "__main__":
    demo.launch()