"""
核心压缩器模块 - SmartCompressor主类

提供统一的文本压缩接口，支持多种策略、格式和配置选项。
"""

import os
import sys
from typing import Optional, Dict, List, Union, Callable
from pathlib import Path

from .strategies import (
    CompressionStrategy,
    CompressionResult,
    SummarizeStrategy,
    KeywordExtractStrategy,
    SemanticDeduplicateStrategy,
    CodeMinifyStrategy,
    HybridStrategy,
)
from .token_counter import TokenCounter
from .format_handlers import FormatHandlerRegistry


class SmartCompressor:
    """
    智能文本压缩器

    核心功能:
    - 多种压缩策略（摘要、关键词、去重、代码精简、混合）
    - 精确的Token计数
    - 多格式文件支持
    - 流式处理大文件
    - 预算控制（Token预算管理）

    使用示例:
        >>> compressor = SmartCompressor(strategy='hybrid')
        >>> result = compressor.compress(text, target_ratio=0.5)
        >>> print(f"压缩率: {result.reduction_ratio}%")
    """

    STRATEGIES = {
        'summarize': SummarizeStrategy,
        'keyword': KeywordExtractStrategy,
        'dedup': SemanticDeduplicateStrategy,
        'code': CodeMinifyStrategy,
        'hybrid': HybridStrategy,
    }

    def __init__(
        self,
        strategy: str = 'hybrid',
        model: str = 'cl100k_base',
        token_counter: Optional[TokenCounter] = None,
    ):
        """
        初始化压缩器

        Args:
            strategy: 压缩策略名称 ('summarize', 'keyword', 'dedup', 'code', 'hybrid')
            model: Tokenizer模型名称
            token_counter: 自定义TokenCounter实例
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {list(self.STRATEGIES.keys())}")

        self.strategy_name = strategy
        self.strategy: CompressionStrategy = self.STRATEGIES[strategy]()
        self.token_counter = token_counter or TokenCounter(model)
        self.format_registry = FormatHandlerRegistry()

    def compress(
        self,
        text: str,
        target_ratio: float = 0.5,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompressionResult:
        """
        压缩文本

        Args:
            text: 原始文本
            target_ratio: 目标压缩率 (0-1)，压缩后保留的比例
            max_tokens: 最大Token限制（优先于target_ratio）
            **kwargs: 额外参数传递给策略

        Returns:
            CompressionResult: 压缩结果
        """
        if not text or not text.strip():
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=0,
                compressed_tokens=0,
                strategy_name=self.strategy_name,
            )

        # 如果指定了max_tokens，计算target_ratio
        if max_tokens is not None:
            original_tokens = self.token_counter.count(text)
            if original_tokens > 0:
                target_ratio = min(max_tokens / original_tokens, 1.0)
            else:
                target_ratio = 1.0

        # 执行压缩
        result = self.strategy.compress(text, target_ratio, **kwargs)

        # 使用精确的token计数更新结果
        result.original_tokens = self.token_counter.count(result.original_text)
        result.compressed_tokens = self.token_counter.count(result.compressed_text)

        return result

    def compress_file(
        self,
        filepath: str,
        target_ratio: float = 0.5,
        max_tokens: Optional[int] = None,
        output_path: Optional[str] = None,
        **kwargs
    ) -> CompressionResult:
        """
        压缩文件

        Args:
            filepath: 输入文件路径
            target_ratio: 目标压缩率
            max_tokens: 最大Token限制
            output_path: 输出文件路径（可选）
            **kwargs: 额外参数

        Returns:
            CompressionResult: 压缩结果
        """
        # 读取文件
        text = self.format_registry.extract_text(filepath)

        # 获取文件元数据
        metadata = self.format_registry.get_metadata(filepath)
        language = self.format_registry.get_language(filepath)

        # 检测文件类型并调整策略
        if language and self.strategy_name == 'hybrid':
            kwargs['language'] = language

        # 压缩
        result = self.compress(text, target_ratio, max_tokens, **kwargs)

        # 添加文件元数据
        if result.metadata is None:
            result.metadata = {}
        result.metadata['file_info'] = metadata

        # 保存到文件
        if output_path:
            self._save_to_file(result.compressed_text, output_path)

        return result

    def compress_batch(
        self,
        filepaths: List[str],
        target_ratio: float = 0.5,
        max_tokens: Optional[int] = None,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> List[CompressionResult]:
        """
        批量压缩文件

        Args:
            filepaths: 文件路径列表
            target_ratio: 目标压缩率
            max_tokens: 最大Token限制
            output_dir: 输出目录（可选）
            **kwargs: 额外参数

        Returns:
            List[CompressionResult]: 压缩结果列表
        """
        results = []
        for filepath in filepaths:
            try:
                output_path = None
                if output_dir:
                    filename = os.path.basename(filepath)
                    name, ext = os.path.splitext(filename)
                    output_path = os.path.join(output_dir, f"{name}.compressed{ext}")

                result = self.compress_file(filepath, target_ratio, max_tokens, output_path, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error compressing {filepath}: {e}")
                # 创建错误结果
                results.append(CompressionResult(
                    original_text="",
                    compressed_text="",
                    original_tokens=0,
                    compressed_tokens=0,
                    strategy_name=self.strategy_name,
                    metadata={"error": str(e), "filepath": filepath},
                ))

        return results

    def stream_compress(
        self,
        filepath: str,
        chunk_size: int = 4000,
        target_ratio: float = 0.5,
        callback: Optional[Callable[[CompressionResult], None]] = None,
        **kwargs
    ) -> List[CompressionResult]:
        """
        流式压缩大文件

        将大文件分块处理，每块单独压缩。

        Args:
            filepath: 文件路径
            chunk_size: 每块的token数量
            target_ratio: 目标压缩率
            callback: 每块处理后的回调函数
            **kwargs: 额外参数

        Returns:
            List[CompressionResult]: 每块的压缩结果
        """
        results = []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            buffer = []
            buffer_tokens = 0

            for line in f:
                line_tokens = self.token_counter.count(line)

                if buffer_tokens + line_tokens > chunk_size and buffer:
                    # 压缩当前块
                    chunk_text = ''.join(buffer)
                    result = self.compress(chunk_text, target_ratio, **kwargs)
                    results.append(result)

                    if callback:
                        callback(result)

                    # 重置缓冲区
                    buffer = [line]
                    buffer_tokens = line_tokens
                else:
                    buffer.append(line)
                    buffer_tokens += line_tokens

            # 处理最后一块
            if buffer:
                chunk_text = ''.join(buffer)
                result = self.compress(chunk_text, target_ratio, **kwargs)
                results.append(result)

                if callback:
                    callback(result)

        return results

    def get_token_stats(self, text: str) -> Dict:
        """获取文本的Token统计信息"""
        return self.token_counter.get_stats(text)

    def estimate_compression(self, text: str, target_ratio: float = 0.5) -> Dict:
        """
        预估压缩效果（不实际执行压缩）

        Args:
            text: 原始文本
            target_ratio: 目标压缩率

        Returns:
            Dict: 预估结果
        """
        stats = self.get_token_stats(text)
        estimated_tokens = int(stats['token_count'] * target_ratio)

        return {
            "original_tokens": stats['token_count'],
            "estimated_tokens": estimated_tokens,
            "estimated_reduction": f"{round((1 - target_ratio) * 100, 1)}%",
            "strategy": self.strategy_name,
            "model": stats['model'],
        }

    def _save_to_file(self, text: str, filepath: str):
        """保存文本到文件"""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出可用的压缩策略"""
        return list(cls.STRATEGIES.keys())

    @classmethod
    def list_supported_formats(cls) -> List[str]:
        """列出支持的文件格式"""
        registry = FormatHandlerRegistry()
        return registry.list_supported_formats()
