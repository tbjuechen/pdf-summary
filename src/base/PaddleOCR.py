import base64
import os
import shutil
import requests
from typing import Optional, Dict, List, Any
from loguru import logger

class PaddleOCRClient:
    """
    PaddleOCR 布局分析客户端封装
    """
    DEFAULT_API_URL = "https://j4x8mcmanbi1i7bd.aistudio-app.com/layout-parsing"

    def __init__(self, api_url: Optional[str] = None, token: Optional[str] = None):
        """
        初始化客户端
        :param api_url: API 地址，默认使用环境变量 PADDLE_OCR_API_URL 或内置默认值
        :param token: API Token，默认使用环境变量 PADDLE_OCR_TOKEN 或内置默认值
        """
        self.api_url = api_url or os.getenv("PADDLE_OCR_API_URL", self.DEFAULT_API_URL)
        self.token = token or os.getenv("PADDLE_OCR_TOKEN")
        
        if not self.token:
            raise ValueError("Token must be provided via argument or environment variable PADDLE_OCR_TOKEN")

    def parse(self, file_path: str, output_dir: str = "output", **kwargs) -> List[str]:
        """
        解析文件并保存结果
        :param file_path: PDF 或图片文件路径
        :param output_dir: 结果输出根目录，默认为 "output"
        :param kwargs: 可选参数，如 useDocOrientationClassify, useDocUnwarping, useChartRecognition
        :return: 生成的 Markdown 文件路径列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 确定输出目录: output_dir/文件名/
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(output_dir, file_name)

        # 如果目录存在，先删除再创建
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # 确定文件类型: 0 for PDF, 1 for images
        ext = os.path.splitext(file_path)[1].lower()
        file_type = 0 if ext == '.pdf' else 1

        # 读取并编码文件
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "file": file_data,
            "fileType": file_type,
            "useDocOrientationClassify": kwargs.get("useDocOrientationClassify", False),
            "useDocUnwarping": kwargs.get("useDocUnwarping", False),
            "useChartRecognition": kwargs.get("useChartRecognition", False),
        }

        logger.info(f"[PaddleOCR] Sending request to {self.api_url} for file {file_path}...")
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        result = response.json().get("result", {})
        if not result:
            logger.warning("[PaddleOCR] No result found in response.")
            return []

        generated_files = []
        full_markdown_texts = []

        layout_results = result.get("layoutParsingResults", [])
        for i, res in enumerate(layout_results):
            text_content = res["markdown"]["text"]
            full_markdown_texts.append(text_content)

            # 保存 Markdown
            md_filename = os.path.join(output_dir, f"doc_{i}.md")
            with open(md_filename, "w", encoding="utf-8") as md_file:
                md_file.write(text_content)
            generated_files.append(md_filename)
            logger.debug(f"[PaddleOCR] Markdown document saved at {md_filename}")

            # 保存 Markdown 中引用的图片
            if "images" in res["markdown"]:
                self._save_images(res["markdown"]["images"], output_dir)
            
            # 保存输出的分析图片
            if "outputImages" in res:
                self._save_remote_images(res["outputImages"], output_dir, suffix=f"_{i}")

        # 保存合并后的 Markdown
        if full_markdown_texts:
            full_md_filename = os.path.join(output_dir, "doc.md")
            with open(full_md_filename, "w", encoding="utf-8") as f:
                f.write("\n\n".join(full_markdown_texts))
            generated_files.append(full_md_filename)
            logger.info(f"[PaddleOCR] Full markdown document saved at {full_md_filename}")

        return generated_files

    def _save_images(self, images_map: Dict[str, str], output_dir: str):
        """下载并保存 Markdown 中的图片"""
        for img_path, img_url in images_map.items():
            full_img_path = os.path.join(output_dir, img_path)
            os.makedirs(os.path.dirname(full_img_path), exist_ok=True)
            try:
                img_bytes = requests.get(img_url).content
                with open(full_img_path, "wb") as img_file:
                    img_file.write(img_bytes)
                logger.debug(f"[PaddleOCR] Image saved to: {full_img_path}")
            except Exception as e:
                logger.error(f"[PaddleOCR] Failed to save image {img_path}: {e}")

    def _save_remote_images(self, images_map: Dict[str, str], output_dir: str, suffix: str = ""):
        """下载并保存结果图片"""
        for img_name, img_url in images_map.items():
            try:
                img_response = requests.get(img_url)
                if img_response.status_code == 200:
                    filename = os.path.join(output_dir, f"{img_name}{suffix}.jpg")
                    with open(filename, "wb") as f:
                        f.write(img_response.content)
                    logger.debug(f"[PaddleOCR] Image saved to: {filename}")
                else:
                    logger.error(f"[PaddleOCR] Failed to download image {img_name}, status code: {img_response.status_code}")
            except Exception as e:
                logger.error(f"[PaddleOCR] Error downloading image {img_name}: {e}")

if __name__ == "__main__":
    # 示例用法
    import dotenv
    dotenv.load_dotenv()

    file_path = "data/PDF-example.pdf"
    if os.path.exists(file_path):
        client = PaddleOCRClient()
        try:
            files = client.parse(file_path)
            logger.success(f"[PaddleOCR] Successfully processed. Generated files: {files}")
        except Exception as e:
            logger.error(f"[PaddleOCR] Error processing file: {e}")
    else:
        logger.warning(f"[PaddleOCR] Example file not found: {file_path}")