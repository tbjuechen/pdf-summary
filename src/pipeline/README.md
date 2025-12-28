## pdf处理
- **输入**：pdf文件
- **输出**：结构化文档分片，包括`image`,`text`等

### PaddleOCR 输出处理模块
- 调用 PaddleOCR 服务解析 PDF 文档。
- 将解析结果归档至 PDF_Extraction/<pdf_name>/ 目录，仅保留 doc.md 与 images 图像资源。
- 返回包含 Markdown 内容与图片元数据的 Document 对象，供后续步骤使用。

### 文本增强模块
- MarkdownReferenceCleaner 会扫描 doc.md 中的二级标题。
- 命中 “## References” 或 “## 参考文献” 等标题后，连同其后内容全部移除。
- 处理结果会同步更新磁盘上的 doc.md 并写回 Document 内容。

### 文档构建模块
- MarkdownDocumentBuilder 解析 doc.md 中的 `<img>` 标签，加载 imgs 目录下的对应图片。
- 使用 utils.img2base64 将图片编码为 Base64 字符串，填入 ImageData.data，并记录绝对路径与 relative_path 元数据。
- 汇总图像列表并配合 Markdown 文本生成 Document，metadata 保持为空，doc_id 根据全文哈希自动生成。

### 文档切片模块
- MarkdownChunkBuilder 按行匹配 `## 1.` 或 `### 1.` 等模式进行章节切片，避开 `## 1.1`。
- 第一个匹配之前的内容作为首块，其余依次按标题划分，每块内容封装为 DocumentChunk。
- chunk 的 doc_id 继承自原文档，chunk_index 按出现顺序递增。