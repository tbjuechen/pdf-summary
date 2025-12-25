import pytest
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
from base.PaddleOCR import PaddleOCRClient

class TestPaddleOCRClient:

    @pytest.fixture
    def mock_env(self, monkeypatch):
        monkeypatch.setenv("PADDLE_OCR_TOKEN", "test-token")
        monkeypatch.setenv("PADDLE_OCR_API_URL", "https://api.test.com")

    @pytest.fixture
    def client(self, mock_env):
        return PaddleOCRClient()

    def test_init(self, mock_env):
        client = PaddleOCRClient()
        assert client.token == "test-token"
        assert client.api_url == "https://api.test.com"

    def test_init_missing_token(self, monkeypatch):
        monkeypatch.delenv("PADDLE_OCR_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Token must be provided"):
            PaddleOCRClient()

    def test_parse_file_not_found(self, client):
        import asyncio
        async def run_test():
            with patch("os.path.exists", return_value=False):
                with pytest.raises(FileNotFoundError):
                    await client.parse("non_existent.pdf")
        asyncio.run(run_test())

    def test_parse_success(self, client):
        import asyncio
        async def run_test():
            # 模拟 API 响应数据
            mock_api_response = {
                "result": {
                    "layoutParsingResults": [
                        {
                            "markdown": {
                                "text": "# Page 1",
                                "images": {"img1.jpg": "http://img.com/1.jpg"}
                            },
                            "outputImages": {"layout.jpg": "http://img.com/layout.jpg"}
                        }
                    ]
                }
            }

            # Mock 依赖
            with patch("os.path.exists", side_effect=lambda p: p == "test.pdf"), \
                 patch("builtins.open", mock_open(read_data=b"pdf-content")) as mock_file, \
                 patch("os.makedirs") as mock_makedirs, \
                 patch("shutil.rmtree") as mock_rmtree, \
                 patch("httpx.AsyncClient") as mock_httpx_cls:

                # 设置 httpx Mock
                mock_client_instance = AsyncMock()
                mock_httpx_cls.return_value.__aenter__.return_value = mock_client_instance
                
                # 模拟 POST 响应
                mock_post_response = MagicMock()
                mock_post_response.status_code = 200
                mock_post_response.json.return_value = mock_api_response
                mock_client_instance.post.return_value = mock_post_response

                # 模拟 GET 响应 (图片下载)
                mock_get_response = MagicMock()
                mock_get_response.status_code = 200
                mock_get_response.content = b"image-content"
                mock_client_instance.get.return_value = mock_get_response

                # 执行测试
                files = await client.parse("test.pdf", output_dir="out")

                # 验证结果
                assert len(files) == 2 # doc_0.md 和 doc.md
                assert "out/test/doc_0.md" in files
                assert "out/test/doc.md" in files

                # 验证 API 调用
                mock_client_instance.post.assert_called_once()
                
                # 验证图片下载调用 (1个内容图 + 1个布局图)
                assert mock_client_instance.get.call_count == 2
                
                # 验证文件写入
                # 1. 读取PDF
                # 2. 写入 doc_0.md
                # 3. 写入 img1.jpg
                # 4. 写入 layout_0.jpg
                # 5. 写入 doc.md
                assert mock_file.call_count >= 5
        asyncio.run(run_test())

    def test_parse_api_error(self, client):
        import asyncio
        async def run_test():
            with patch("os.path.exists", side_effect=lambda p: p == "test.pdf"), \
                 patch("builtins.open", mock_open(read_data=b"pdf-content")), \
                 patch("os.makedirs"), \
                 patch("httpx.AsyncClient") as mock_httpx_cls:

                mock_client_instance = AsyncMock()
                mock_httpx_cls.return_value.__aenter__.return_value = mock_client_instance
                
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_client_instance.post.return_value = mock_response

                with pytest.raises(Exception, match="API request failed"):
                    await client.parse("test.pdf")
        asyncio.run(run_test())

    def test_parse_no_result(self, client):
        import asyncio
        async def run_test():
            with patch("os.path.exists", side_effect=lambda p: p == "test.pdf"), \
                 patch("builtins.open", mock_open(read_data=b"pdf-content")), \
                 patch("os.makedirs"), \
                 patch("httpx.AsyncClient") as mock_httpx_cls:

                mock_client_instance = AsyncMock()
                mock_httpx_cls.return_value.__aenter__.return_value = mock_client_instance
                
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"result": {}} # 空结果
                mock_client_instance.post.return_value = mock_response

                files = await client.parse("test.pdf")
                assert files == []
        asyncio.run(run_test())
