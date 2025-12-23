import os
import sys
import base64

def img2base64(image_path: str) -> str:
    """
    将图片文件转换为Base64编码字符串。
    
    :param image_path: 图片文件的路径。
    :return: Base64编码的字符串。
    :rtype: str
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')