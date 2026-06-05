"""
压缩策略模块 - 提供多种文本压缩算法

包含策略:
- SummarizeStrategy: 智能摘要压缩
- KeywordExtractStrategy: 关键词提取压缩
- SemanticDeduplicateStrategy: 语义去重压缩
- CodeMinifyStrategy: 代码精简压缩
- HybridStrategy: 混合策略（自动选择最优策略）
"""

import re
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """压缩结果数据类"""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    strategy_name: str
    metadata: Dict = None

    @property
    def reduction_ratio(self) -> float:
        """计算压缩率"""
        if self.original_tokens == 0:
            return 0.0
        return round((self.original_tokens - self.compressed_tokens) / self.original_tokens * 100, 2)

    @property
    def savings_ratio(self) -> float:
        """计算节省比例"""
        return self.reduction_ratio

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "strategy": self.strategy_name,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "reduction_ratio": f"{self.reduction_ratio}%",
            "metadata": self.metadata or {},
        }


class CompressionStrategy(ABC):
    """压缩策略抽象基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        """
        压缩文本

        Args:
            text: 原始文本
            target_ratio: 目标压缩率 (0-1)
            **kwargs: 额外参数

        Returns:
            CompressionResult: 压缩结果
        """
        pass

    def _count_tokens_simple(self, text: str) -> int:
        """简单token计数（用于内部估算）"""
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return len(tokens)


class SummarizeStrategy(CompressionStrategy):
    """
    智能摘要压缩策略

    通过提取关键句子和段落，生成精简的摘要版本。
    适用于长文本、文章、报告等。
    """

    def __init__(self):
        super().__init__("summarize")

    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        original_tokens = self._count_tokens_simple(text)

        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            return CompressionResult(text, text, original_tokens, original_tokens, self.name)

        # 计算每个段落的重要性分数
        scored_paragraphs = self._score_paragraphs(paragraphs)

        # 根据目标压缩率选择段落
        target_length = int(original_tokens * target_ratio)
        selected = self._select_paragraphs(scored_paragraphs, target_length)

        # 合并选中的段落
        compressed = '\n\n'.join(selected)
        compressed_tokens = self._count_tokens_simple(compressed)

        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.name,
            metadata={
                "paragraphs_total": len(paragraphs),
                "paragraphs_selected": len(selected),
                "scoring_method": "keyword_density + position",
            }
        )

    def _score_paragraphs(self, paragraphs: List[str]) -> List[Tuple[str, float]]:
        """为段落打分"""
        # 提取所有关键词
        all_words = ' '.join(paragraphs).lower()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_words)
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1

        scored = []
        for i, para in enumerate(paragraphs):
            score = 0.0

            # 位置权重（开头和结尾更重要）
            if i == 0:
                score += 10
            elif i == len(paragraphs) - 1:
                score += 5

            # 关键词密度
            para_words = re.findall(r'\b[a-zA-Z]{4,}\b', para.lower())
            if para_words:
                keyword_score = sum(word_freq.get(w, 0) for w in para_words) / len(para_words)
                score += keyword_score

            # 长度惩罚（过短的段落可能不重要）
            if len(para) < 50:
                score *= 0.5

            scored.append((para, score))

        # 按分数排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _select_paragraphs(self, scored_paragraphs: List[Tuple[str, float]], target_length: int) -> List[str]:
        """选择段落以达到目标长度"""
        selected = []
        current_length = 0

        for para, score in scored_paragraphs:
            para_tokens = self._count_tokens_simple(para)
            if current_length + para_tokens <= target_length or not selected:
                selected.append(para)
                current_length += para_tokens
            if current_length >= target_length:
                break

        # 保持原始顺序
        # 这里简化处理，实际应该记录原始索引
        return selected


class KeywordExtractStrategy(CompressionStrategy):
    """
    关键词提取压缩策略

    提取文本中的关键信息和实体，去除冗余描述。
    适用于信息密集型文本、笔记、文档等。
    """

    def __init__(self):
        super().__init__("keyword_extract")

    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        original_tokens = self._count_tokens_simple(text)

        # 提取关键信息
        lines = text.split('\n')
        compressed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 保留标题行
            if self._is_heading(line):
                compressed_lines.append(line)
                continue

            # 提取关键短语
            key_phrases = self._extract_key_phrases(line)
            if key_phrases:
                compressed_lines.append(' · '.join(key_phrases))

        compressed = '\n'.join(compressed_lines)
        if not compressed:
            compressed = text[:int(len(text) * target_ratio)]

        compressed_tokens = self._count_tokens_simple(compressed)

        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.name,
            metadata={
                "lines_processed": len(lines),
                "lines_kept": len(compressed_lines),
            }
        )

    def _is_heading(self, line: str) -> bool:
        """判断是否为标题行"""
        # Markdown标题
        if re.match(r'^#{1,6}\s', line):
            return True
        # 全大写短行
        if line.isupper() and len(line) < 100:
            return True
        # 以冒号结尾的短行
        if len(line) < 80 and line.endswith(':'):
            return True
        return False

    def _extract_key_phrases(self, line: str) -> List[str]:
        """提取关键短语"""
        phrases = []

        # 提取引号内容
        quotes = re.findall(r'["""\']([^"""\']{10,200})["""\']', line)
        phrases.extend(quotes)

        # 提取关键名词短语（简化版）
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', line)
        if words:
            phrases.extend(words[:3])

        # 提取数字和度量
        numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:%|MB|GB|ms|s|kg|km|USD|\$)?\b', line)
        if numbers:
            phrases.extend(numbers[:2])

        # 去重并限制长度
        seen = set()
        result = []
        for p in phrases:
            if p not in seen and len(p) > 5:
                seen.add(p)
                result.append(p)
                if len(result) >= 5:
                    break

        return result


class SemanticDeduplicateStrategy(CompressionStrategy):
    """
    语义去重压缩策略

    识别并合并语义相似的句子，去除重复信息。
    适用于日志、聊天记录、重复性文档等。
    """

    def __init__(self):
        super().__init__("semantic_dedup")

    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        original_tokens = self._count_tokens_simple(text)

        # 分句
        sentences = self._split_sentences(text)

        # 去重
        unique_sentences = self._deduplicate(sentences)

        compressed = ' '.join(unique_sentences)
        compressed_tokens = self._count_tokens_simple(compressed)

        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.name,
            metadata={
                "sentences_original": len(sentences),
                "sentences_unique": len(unique_sentences),
                "duplicates_removed": len(sentences) - len(unique_sentences),
            }
        )

    def _split_sentences(self, text: str) -> List[str]:
        """将文本分割为句子/行"""
        # 对于日志类文本，按行分割更合适
        lines = text.split('\n')
        sentences = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                sentences.append(line)
        return sentences

    def _deduplicate(self, sentences: List[str]) -> List[str]:
        """语义去重"""
        if not sentences:
            return []

        unique = []
        seen_signatures = []

        for sent in sentences:
            # 生成语义签名（简化版：小写+去除标点的关键词集合）
            signature = self._generate_signature(sent)

            # 检查是否相似
            is_duplicate = False
            for seen_sig in seen_signatures:
                if self._similarity(signature, seen_sig) > 0.7:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(sent)
                seen_signatures.append(signature)

        return unique

    def _generate_signature(self, text: str) -> str:
        """生成文本签名"""
        # 小写、去除标点、提取关键词
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        words = sorted(set(w for w in cleaned.split() if len(w) > 3))
        return ' '.join(words)

    def _similarity(self, sig1: str, sig2: str) -> float:
        """计算签名相似度"""
        words1 = set(sig1.split())
        words2 = set(sig2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


class CodeMinifyStrategy(CompressionStrategy):
    """
    代码精简压缩策略

    去除代码中的注释、空行、多余空格，保留核心逻辑。
    适用于源代码文件、配置文件等。
    """

    def __init__(self):
        super().__init__("code_minify")

    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        original_tokens = self._count_tokens_simple(text)

        language = kwargs.get('language', 'auto')
        if language == 'auto':
            language = self._detect_language(text)

        # 根据语言选择压缩方法
        if language in ['python', 'py']:
            compressed = self._minify_python(text)
        elif language in ['javascript', 'js', 'typescript', 'ts']:
            compressed = self._minify_js(text)
        elif language in ['json']:
            compressed = self._minify_json(text)
        elif language in ['markdown', 'md']:
            compressed = self._minify_markdown(text)
        else:
            compressed = self._minify_generic(text)

        compressed_tokens = self._count_tokens_simple(compressed)

        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy_name=self.name,
            metadata={
                "detected_language": language,
                "methods_applied": ["remove_comments", "remove_empty_lines", "compress_whitespace"],
            }
        )

    def _detect_language(self, text: str) -> str:
        """自动检测编程语言"""
        stripped = text.strip()
        # Python检测
        if re.search(r'(^\s*import\s+\w+|^\s*from\s+\w+\s+import|^\s*def\s+\w+\s*\(|^\s*class\s+\w+)', text, re.M):
            return 'python'
        # JavaScript/TypeScript检测
        elif re.search(r'^\s*(const|let|var|function|=>)', text, re.M):
            return 'javascript'
        # JSON检测
        elif stripped.startswith('{') or stripped.startswith('['):
            try:
                json.loads(text)
                return 'json'
            except:
                pass
        # Markdown检测
        elif re.search(r'^#{1,6}\s', text, re.M):
            return 'markdown'
        return 'generic'

    def _minify_python(self, code: str) -> str:
        """精简Python代码"""
        lines = code.split('\n')
        result = []
        in_multiline_string = False
        string_delim = None

        for line in lines:
            original_line = line
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                continue

            # 处理多行字符串
            if in_multiline_string:
                if string_delim in line:
                    in_multiline_string = False
                    string_delim = None
                continue

            if '"""' in stripped:
                parts = stripped.split('"""')
                if len(parts) % 2 == 0:
                    in_multiline_string = True
                    string_delim = '"""'
                    continue
                else:
                    # 同一行开始和结束
                    line = line[:line.index('"""')]
                    stripped = line.strip()

            if "'''" in stripped:
                parts = stripped.split("'''")
                if len(parts) % 2 == 0:
                    in_multiline_string = True
                    string_delim = "'''"
                    continue
                else:
                    line = line[:line.index("'''")]
                    stripped = line.strip()

            # 跳过纯注释行
            if stripped.startswith('#'):
                continue

            # 去除行内注释（注意避免字符串中的#）
            new_line = self._remove_inline_comment(line)

            if new_line.strip():
                result.append(new_line.rstrip())

        return '\n'.join(result)

    def _remove_inline_comment(self, line: str) -> str:
        """安全地移除行内注释"""
        in_string = False
        string_char = None
        i = 0
        while i < len(line):
            c = line[i]
            if not in_string and c in ('"', "'"):
                in_string = True
                string_char = c
            elif in_string and c == string_char:
                # 检查是否是转义
                if i > 0 and line[i-1] != '\\':
                    in_string = False
                    string_char = None
            elif not in_string and c == '#':
                return line[:i]
            i += 1
        return line

    def _minify_js(self, code: str) -> str:
        """精简JavaScript/TypeScript代码"""
        # 移除多行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # 移除单行注释
        lines = code.split('\n')
        result = []
        for line in lines:
            if '//' in line:
                line = line[:line.index('//')]
            if line.strip():
                result.append(line.rstrip())
        return '\n'.join(result)

    def _minify_json(self, text: str) -> str:
        """精简JSON"""
        try:
            data = json.loads(text)
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        except:
            return self._minify_generic(text)

    def _minify_markdown(self, text: str) -> str:
        """精简Markdown"""
        lines = text.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            # 保留标题和列表
            if stripped.startswith('#') or stripped.startswith('-') or stripped.startswith('*'):
                result.append(stripped)
            # 保留非空段落行
            elif stripped and len(stripped) > 10:
                result.append(stripped)
        return '\n'.join(result)

    def _minify_generic(self, text: str) -> str:
        """通用精简"""
        # 压缩连续空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除行尾空格
        lines = [line.rstrip() for line in text.split('\n')]
        return '\n'.join(line for line in lines if line.strip())


class HybridStrategy(CompressionStrategy):
    """
    混合压缩策略

    自动分析文本类型，选择最优的压缩策略组合。
    智能识别文本类型并应用最佳压缩方案。
    """

    def __init__(self):
        super().__init__("hybrid")
        self.strategies = {
            'summarize': SummarizeStrategy(),
            'keyword': KeywordExtractStrategy(),
            'dedup': SemanticDeduplicateStrategy(),
            'code': CodeMinifyStrategy(),
        }

    def compress(self, text: str, target_ratio: float = 0.5, **kwargs) -> CompressionResult:
        original_tokens = self._count_tokens_simple(text)

        # 分析文本类型
        text_type = self._analyze_text_type(text)

        # 选择策略
        if text_type == 'code':
            result = self.strategies['code'].compress(text, target_ratio, **kwargs)
            # 如果压缩不够，再应用去重
            if result.reduction_ratio < (1 - target_ratio) * 100:
                result2 = self.strategies['dedup'].compress(result.compressed_text, target_ratio)
                result = CompressionResult(
                    original_text=text,
                    compressed_text=result2.compressed_text,
                    original_tokens=original_tokens,
                    compressed_tokens=result2.compressed_tokens,
                    strategy_name=self.name,
                    metadata={
                        "text_type": text_type,
                        "sub_strategies": ["code", "dedup"],
                        "stage1": result.to_dict(),
                        "stage2": result2.to_dict(),
                    }
                )
        elif text_type == 'log':
            result = self.strategies['dedup'].compress(text, target_ratio, **kwargs)
        elif text_type == 'article':
            result = self.strategies['summarize'].compress(text, target_ratio, **kwargs)
        elif text_type == 'notes':
            result = self.strategies['keyword'].compress(text, target_ratio, **kwargs)
        else:
            # 通用文本：先摘要再去重
            result1 = self.strategies['summarize'].compress(text, target_ratio * 1.2)
            result2 = self.strategies['dedup'].compress(result1.compressed_text, target_ratio)
            result = CompressionResult(
                original_text=text,
                compressed_text=result2.compressed_text,
                original_tokens=original_tokens,
                compressed_tokens=result2.compressed_tokens,
                strategy_name=self.name,
                metadata={
                    "text_type": text_type,
                    "sub_strategies": ["summarize", "dedup"],
                }
            )

        return result

    def _analyze_text_type(self, text: str) -> str:
        """分析文本类型"""
        # 代码检测
        code_patterns = [
            r'^\s*(def|class|import|from|function|const|let|var|if|for|while)\s',
            r'[{};]\s*$',
            r'^\s*#.*|^\s*//.*',
        ]
        code_score = sum(1 for p in code_patterns if re.search(p, text, re.M))

        # 日志检测
        log_patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\[\w+\]\s*\w+',
            r'(INFO|DEBUG|WARN|ERROR|FATAL)',
        ]
        log_score = sum(1 for p in log_patterns if re.search(p, text))

        # 文章检测
        article_patterns = [
            r'^#{1,6}\s',
            r'\n\n',
            r'[.!?]\s+',
        ]
        article_score = sum(1 for p in article_patterns if re.search(p, text))

        scores = {
            'code': code_score,
            'log': log_score,
            'article': article_score,
        }

        max_type = max(scores, key=scores.get)
        if scores[max_type] == 0:
            return 'generic'
        return max_type
