import re
import os

def parse_markdown_by_headers(content):
    """
    正则解析逻辑：匹配 #, ##, ### 开头的标题及其随后的内容
    """
    pattern = re.compile(r'(?m)(^#{1,3}\s+.*$)([\s\S]*?)(?=^#{1,3}\s+|\Z)')
    matches = pattern.findall(content)
    
    sections = []
    for title, text in matches:
        sections.append({
            "title": title.strip(),
            "content": text.strip()
        })
    return sections

if __name__ == "__main__":
    # 1. 设置文件路径
    file_path = r"C:\Users\Yeyan\Desktop\PDF_extraction\pdf-summary\PDF_example.pdf_by_PaddleOCR-VL.md"

    # 2. 读取文件
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 3. 执行解析
            parsed_sections = parse_markdown_by_headers(content)
            
            print(f"解析完成，共找到 {len(parsed_sections)} 个部分：\n")
            print("-" * 50)

            # 4. 简单遍历打印：标题 + 内容前50字
            for i, section in enumerate(parsed_sections):
                title = section['title']
                # 获取内容前50个字，并将换行符替换为空格，保持在一行显示
                preview = section['content'][:50].replace('\n', ' ')
                
                print(f"[{i}] 标题: {title}")
                print(f"    内容: {preview}...")
                print("-" * 50)

        except Exception as e:
            print(f"读取或解析出错: {e}")
    else:
        print(f"文件不存在: {file_path}")