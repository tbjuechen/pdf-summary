import os
import sys
import json
import dotenv
from pathlib import Path

# 1. 自动处理路径：确保 Python 能找到 src 目录并加载根目录的 .env
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.append(os.path.join(project_root, "src"))
dotenv.load_dotenv(os.path.join(project_root, ".env"))

# 导入组长写的 LLMClient 类
from base import LLMClient, Message

class PaperSlicer:
    def __init__(self, output_dir="gen_output_debug"):
        """
        初始化切片器
        """
        # 初始化组长的客户端，这里可以按需设置 temperature
        self.client = LLMClient(temperature=0.0)
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def run_slicing(self, file_path):
        """
        执行论文切片主逻辑
        """
        if not os.path.exists(file_path):
            print(f"❌ 找不到文件: {file_path}")
            return

        print(f"📖 读取原文: {file_path} ...")
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # 构建发送给组长 LLMClient 的消息格式
        system_prompt = """
        你是一个科研论文结构分析师。请分析原文，利用【原文切片法】提取文章各个部分的【准确起始片段】和【准确结束片段】。
        
        文章部分包括但不限于：
        01_Abstract, 02_Introduction, 03_Keywords, 04_Related_Work, 05_Methodology, 
        06_Experiments, 07_Results, 08_Discussion, 09_Conclusion, 10_References.
        
        要求：
        1. 返回 JSON，包含 `_thought` 字段。
        2. 每个部分返回 `segments` 数组，包含 `start` 与 `end` 字段。
        3. `start` 和 `end` 必须是原文中完全存在的字符串（建议 20-40 字符）。
        4. 片段必须按原文顺序。
        """

        print(f"🤖 正在调用组长的 LLMClient (模型: {self.client.model})...")

        try:
            # 调用组长的同步聊天接口
            # 传入 response_format 强制要求返回 JSON 对象
            response_msg = self.client.simple_chat(
                system_prompt=system_prompt,
                user_message=f"论文原文如下:\n\n{full_text}",
                response_format={"type": "json_object"}
            )
            
            # 从组长定义的 Message 对象中提取 content
            raw_content = response_msg.content
            
            print("\n" + "="*20 + " 模型原始返回 " + "="*20)
            print(raw_content)
            print("="*50 + "\n")
            
            locators = json.loads(raw_content)

        except Exception as e:
            print(f"❌ API 调用或解析失败: {e}")
            return

        # 执行物理切片
        self._process_locators(full_text, locators)

    def _process_locators(self, full_text, locators):
        """
        根据模型返回的起始和结束字符串，从原文中截取内容
        """
        for section_name, loc in locators.items():
            if section_name == "_thought":
                continue
            
            # 兼容处理：支持 segments 列表或直接包含 start/end 的字典
            segments = loc.get("segments")
            if not segments and loc.get("start") and loc.get("end"):
                segments = [{"start": loc.get("start"), "end": loc.get("end")}]

            if not segments:
                print(f" 🔍 {section_name}: 跳过（无定位信息）")
                continue

            segment_contents = []
            status = "✅ 正常"
            search_pos = 0

            for segment in segments:
                start_str = segment.get("start", "")
                end_str = segment.get("end", "")

                # 在原文中查找位置
                start_idx = full_text.find(start_str, search_pos)
                if start_idx == -1:
                    status = f"❌ 找不到开始标记: {start_str[:20]}"
                    break

                end_idx_temp = full_text.find(end_str, start_idx)
                if end_idx_temp == -1:
                    status = f"❌ 找不到结束标记: {end_str[:20]}"
                    break

                end_idx = end_idx_temp + len(end_str)
                segment_contents.append(full_text[start_idx:end_idx])
                search_pos = end_idx  # 更新搜索位置，避免回溯

            # 保存文件
            if status.startswith("✅"):
                content = "\n\n".join(segment_contents)
                file_name = f"{section_name}.md"
                with open(os.path.join(self.output_dir, file_name), 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f" 📝 {section_name}: {status} (长度: {len(content)})")
            else:
                print(f" 📝 {section_name}: {status}")

# --- 运行入口 ---
if __name__ == "__main__":
    # 替换为你实际的文件名
    input_file = 'output/PDF-example/doc.md'
    
    slicer = PaperSlicer()
    slicer.run_slicing(input_file)