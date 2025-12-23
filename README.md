# PDF总结助手
## 技术路线
- 模型：qwen？
- pdf解析：[PaddleOCR](https://aistudio.baidu.com/paddleocr/task)
- ui：Gradio？
## 代码架构
- 基础设施层
  - PaddleOCR接口
  - 大模型（Message, Client）
- PDF Pipeline
  - 调用 PaddleOCR 解析结果
  - 文本增强（去除页眉页脚等）
  - 图片索引（索引到文本引用位置）
  - 文本分片（根据 markdown 标签）
- 应用层
  - 文本块分析
  - 图片分析（？
  - 全文解析
  - UI界面
- utils
  - img2base64
## 开发流程
为了防止main分支混乱，请在分支中完成开发，并通过pr合并到master。
1. 环境配置
```bash
git clone https://github.com/tbjuechen/pdf-summary.git
cd pdf-summary
pip install -r requirements.txt
```
2. 切换到开发分支
分支名推荐：
- 新特性：`feature/xxx`
- 修复：`fix/xxx`
```bash
git checkout -b <branch-name>
# 修改代码并commit
git push -u origin <branch-name>
```
3. 使用pr合并
在 GitHub 该分支点击`contribute`合并到main分支