"""
Token计数器模块 - 支持多种tokenizer的token计数功能
"""

import re
from typing import Optional, List
from abc import ABC, abstractmethod


class BaseTokenizer(ABC):
    """Tokenizer基类"""

    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """将文本编码为token列表"""
        pass

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """将token列表解码为文本"""
        pass

    def count(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.encode(text))


class TiktokenTokenizer(BaseTokenizer):
    """基于OpenAI tiktoken的tokenizer"""

    def __init__(self, model: str = "cl100k_base"):
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding(model)
            self.model = model
        except ImportError:
            raise ImportError("tiktoken is required. Install with: pip install tiktoken")

    def encode(self, text: str) -> List[int]:
        return self.encoder.encode(text)

    def decode(self, tokens: List[int]) -> str:
        return self.encoder.decode(tokens)


class SimpleTokenizer(BaseTokenizer):
    """简单的fallback tokenizer（基于空格和标点分割）"""

    def encode(self, text: str) -> List[int]:
        # 简单的token化：按空格和标点分割
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return list(range(len(tokens)))

    def decode(self, tokens: List[int]) -> str:
        return ""


class TokenCounter:
    """
    Token计数器 - 支持多种tokenizer后端

    支持:
    - cl100k_base (GPT-4, GPT-3.5-turbo)
    - p50k_base (GPT-3)
    - r50k_base (GPT-3)
    - simple (fallback)
    """

    SUPPORTED_MODELS = {
        "cl100k_base": "GPT-4, GPT-3.5-turbo, text-embedding-ada-002",
        "p50k_base": "GPT-3 (davinci, curie)",
        "r50k_base": "GPT-3 (older models)",
        "p50k_edit": "GPT-3 edit models",
        "simple": "Fallback simple tokenizer",
    }

    def __init__(self, model: str = "cl100k_base"):
        self.model = model
        self._tokenizer = self._create_tokenizer(model)

    def _create_tokenizer(self, model: str) -> BaseTokenizer:
        """创建tokenizer实例"""
        if model == "simple":
            return SimpleTokenizer()

        try:
            return TiktokenTokenizer(model)
        except ImportError:
            print("Warning: tiktoken not installed, falling back to simple tokenizer")
            return SimpleTokenizer()
        except Exception as e:
            print(f"Warning: Failed to load tokenizer {model}: {e}")
            return SimpleTokenizer()

    def count(self, text: str) -> int:
        """计算文本的token数量"""
        if not text:
            return 0
        return self._tokenizer.count(text)

    def count_file(self, filepath: str) -> int:
        """计算文件的token数量"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return self.count(content)

    def encode(self, text: str) -> List[int]:
        """将文本编码为token列表"""
        return self._tokenizer.encode(text)

    def decode(self, tokens: List[int]) -> str:
        """将token列表解码为文本"""
        return self._tokenizer.decode(tokens)

    def get_stats(self, text: str) -> dict:
        """获取详细的token统计信息"""
        tokens = self.encode(text)
        chars = len(text)
        token_count = len(tokens)

        return {
            "token_count": token_count,
            "char_count": chars,
            "chars_per_token": round(chars / token_count, 2) if token_count > 0 else 0,
            "model": self.model,
        }

    @classmethod
    def list_supported_models(cls) -> dict:
        """列出支持的模型"""
        return cls.SUPPORTED_MODELS.copy()
