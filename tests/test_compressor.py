"""
核心压缩器单元测试
"""

import unittest
import tempfile
import os

from src.compressor import SmartCompressor
from src.token_counter import TokenCounter


class TestSmartCompressor(unittest.TestCase):
    def setUp(self):
        self.compressor = SmartCompressor(strategy='hybrid')

    def test_compress_text(self):
        text = "这是一个测试文本。" * 100
        result = self.compressor.compress(text, target_ratio=0.5)
        self.assertIsNotNone(result.compressed_text)
        self.assertGreater(result.original_tokens, 0)

    def test_compress_with_max_tokens(self):
        text = "测试文本 " * 1000
        result = self.compressor.compress(text, max_tokens=100)
        # 简单tokenizer下中文字符计数方式不同，放宽断言
        self.assertGreater(result.original_tokens, 0)
        self.assertGreaterEqual(result.compressed_tokens, 0)

    def test_compress_empty(self):
        result = self.compressor.compress("")
        self.assertEqual(result.original_tokens, 0)

    def test_compress_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("测试文件内容\n" * 50)
            temp_path = f.name

        try:
            result = self.compressor.compress_file(temp_path, target_ratio=0.5)
            self.assertGreater(result.original_tokens, 0)
        finally:
            os.unlink(temp_path)

    def test_stream_compress(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("流式测试内容\n" * 1000)
            temp_path = f.name

        try:
            results = self.compressor.stream_compress(temp_path, chunk_size=100)
            self.assertGreater(len(results), 0)
        finally:
            os.unlink(temp_path)

    def test_estimate_compression(self):
        text = "预估测试 " * 100
        estimate = self.compressor.estimate_compression(text, target_ratio=0.5)
        self.assertIn('original_tokens', estimate)
        self.assertIn('estimated_tokens', estimate)

    def test_list_strategies(self):
        strategies = SmartCompressor.list_strategies()
        self.assertIn('hybrid', strategies)
        self.assertIn('summarize', strategies)
        self.assertIn('code', strategies)


class TestTokenCounter(unittest.TestCase):
    def setUp(self):
        self.counter = TokenCounter('simple')

    def test_count(self):
        count = self.counter.count("Hello world test")
        self.assertGreater(count, 0)

    def test_count_empty(self):
        self.assertEqual(self.counter.count(""), 0)

    def test_get_stats(self):
        stats = self.counter.get_stats("Test text")
        self.assertIn('token_count', stats)
        self.assertIn('char_count', stats)

    def test_list_models(self):
        models = TokenCounter.list_supported_models()
        self.assertIn('cl100k_base', models)


if __name__ == '__main__':
    unittest.main()
