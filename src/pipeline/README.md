## pdf处理
- **输入**：pdf文件
- **输出**：结构化文档分片，包括`image`,`text`等

### PaddleOCR 输出处理模块
- 调用 PaddleOCR 服务解析 PDF 文档。
- 将解析结果归档至 PDF_Extraction/<pdf_name>/ 目录，仅保留 doc.md 与 images 图像资源。
- 返回包含 Markdown 内容与图片元数据的 Document 对象，供后续步骤使用。