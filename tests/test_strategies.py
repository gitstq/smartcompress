"""
压缩策略单元测试
"""

import unittest
from src.strategies import (
    SummarizeStrategy,
    KeywordExtractStrategy,
    SemanticDeduplicateStrategy,
    CodeMinifyStrategy,
    HybridStrategy,
)


class TestSummarizeStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = SummarizeStrategy()

    def test_compress_article(self):
        text = """
人工智能正在改变我们的世界。

机器学习是人工智能的一个重要分支，它使计算机能够从数据中学习。
深度学习是机器学习的一种方法，使用神经网络来模拟人脑的工作方式。

自然语言处理是人工智能的另一个重要领域，它使计算机能够理解和生成人类语言。
计算机视觉使计算机能够"看到"和理解图像内容。

这些技术正在广泛应用于医疗诊断、自动驾驶、金融分析等领域。
"""
        result = self.strategy.compress(text, target_ratio=0.6)
        self.assertLess(result.compressed_tokens, result.original_tokens)
        self.assertGreater(result.reduction_ratio, 0)

    def test_empty_text(self):
        result = self.strategy.compress("")
        self.assertEqual(result.original_tokens, 0)
        self.assertEqual(result.compressed_tokens, 0)


class TestKeywordExtractStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = KeywordExtractStrategy()

    def test_compress_notes(self):
        text = """
会议记录
时间: 2024年1月15日
参会人员: 张三、李四、王五

讨论内容:
1. 项目进度：目前完成度60%，预计下周完成核心功能开发
2. 技术选型：决定使用Python + FastAPI作为后端框架
3. 预算：当前支出50万元，剩余预算30万元

下一步行动:
- 张三负责API接口设计
- 李四负责数据库优化
- 王五负责前端页面开发
"""
        result = self.strategy.compress(text, target_ratio=0.5)
        self.assertIsNotNone(result.compressed_text)

    def test_heading_detection(self):
        self.assertTrue(self.strategy._is_heading("# 标题"))
        self.assertTrue(self.strategy._is_heading("## 子标题"))
        self.assertTrue(self.strategy._is_heading("SUMMARY:"))
        self.assertFalse(self.strategy._is_heading("这是一段普通文本"))


class TestSemanticDeduplicateStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = SemanticDeduplicateStrategy()

    def test_compress_logs(self):
        text = """
2024-01-15 10:00:01 INFO Server started successfully
2024-01-15 10:00:02 INFO Server started successfully
2024-01-15 10:00:03 INFO Server started successfully
2024-01-15 10:00:04 WARN High memory usage detected
2024-01-15 10:00:05 INFO Server started successfully
2024-01-15 10:00:06 ERROR Database connection failed
2024-01-15 10:00:07 INFO Server started successfully
"""
        result = self.strategy.compress(text, target_ratio=0.5)
        self.assertGreater(result.reduction_ratio, 0)

    def test_similarity(self):
        sig1 = self.strategy._generate_signature("Hello world test")
        sig2 = self.strategy._generate_signature("Hello world example")
        similarity = self.strategy._similarity(sig1, sig2)
        self.assertGreater(similarity, 0)
        self.assertLessEqual(similarity, 1.0)


class TestCodeMinifyStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = CodeMinifyStrategy()

    def test_minify_python(self):
        code = '''
def hello():
    # This is a comment
    print("Hello, World!")
    # Another comment
    return 42

class MyClass:
    """Docstring"""
    def __init__(self):
        self.value = 0
'''
        result = self.strategy.compress(code, target_ratio=0.5)
        self.assertNotIn("# This is a comment", result.compressed_text)
        self.assertIn("def hello():", result.compressed_text)

    def test_detect_language(self):
        py_code = "import os\ndef main():\n    pass"
        self.assertEqual(self.strategy._detect_language(py_code), "python")

        js_code = "const x = 1;\nfunction main() {}"
        self.assertEqual(self.strategy._detect_language(js_code), "javascript")

        json_text = '{"key": "value"}'
        self.assertEqual(self.strategy._detect_language(json_text), "json")


class TestHybridStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = HybridStrategy()

    def test_compress_code(self):
        code = '''
def factorial(n):
    # Calculate factorial
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Test the function
print(factorial(5))
'''
        result = self.strategy.compress(code, target_ratio=0.5)
        self.assertIsNotNone(result.compressed_text)

    def test_compress_article(self):
        text = """
人工智能的发展历史

人工智能的概念最早可以追溯到1950年代。
图灵测试是判断机器是否具有智能的标准。

机器学习是AI的重要分支。
深度学习近年来取得了突破性进展。

未来，AI将在更多领域发挥作用。
"""
        result = self.strategy.compress(text, target_ratio=0.6)
        self.assertGreaterEqual(len(result.compressed_text), 0)


if __name__ == '__main__':
    unittest.main()
