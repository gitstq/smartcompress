"""
SmartCompress - 智能文本压缩与Token优化工具

一个高性能的文本压缩库，专为LLM上下文窗口优化设计。
支持多种压缩策略、智能内容保留、实时流式处理。

版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "SmartCompress Team"

from .compressor import SmartCompressor
from .strategies import (
    SummarizeStrategy,
    KeywordExtractStrategy,
    SemanticDeduplicateStrategy,
    CodeMinifyStrategy,
    HybridStrategy,
)
from .token_counter import TokenCounter
from .format_handlers import FormatHandlerRegistry

__all__ = [
    "SmartCompressor",
    "SummarizeStrategy",
    "KeywordExtractStrategy",
    "SemanticDeduplicateStrategy",
    "CodeMinifyStrategy",
    "HybridStrategy",
    "TokenCounter",
    "FormatHandlerRegistry",
]
