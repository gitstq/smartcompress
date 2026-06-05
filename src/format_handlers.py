"""
格式处理器模块 - 支持多种文件格式的智能处理

支持的格式:
- 文本文件 (.txt, .md, .rst)
- 代码文件 (.py, .js, .ts, .java, .cpp, .c, .go, .rs)
- 数据文件 (.json, .yaml, .yml, .xml, .csv)
- 日志文件 (.log)
- 配置文件 (.ini, .conf, .cfg, .toml)
"""

import os
import re
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class FormatHandler(ABC):
    """格式处理器基类"""

    def __init__(self, extensions: List[str]):
        self.extensions = extensions

    @abstractmethod
    def can_handle(self, filepath: str) -> bool:
        """检查是否能处理该文件"""
        pass

    @abstractmethod
    def extract_text(self, filepath: str) -> str:
        """从文件中提取文本内容"""
        pass

    @abstractmethod
    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        """获取文件元数据"""
        pass

    def get_language(self, filepath: str = "") -> Optional[str]:
        """获取文件对应的编程语言"""
        return None


class TextHandler(FormatHandler):
    """纯文本处理器"""

    def __init__(self):
        super().__init__(['.txt', '.md', '.rst', '.text'])

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.extensions

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        stat = os.stat(filepath)
        return {
            "format": "text",
            "size_bytes": stat.st_size,
            "extension": os.path.splitext(filepath)[1],
        }

    def get_language(self, filepath: str = "") -> Optional[str]:
        return "text"


class CodeHandler(FormatHandler):
    """代码文件处理器"""

    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.mm': 'objective-c',
        '.cs': 'csharp',
        '.fs': 'fsharp',
        '.lua': 'lua',
        '.pl': 'perl',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.vue': 'vue',
        '.svelte': 'svelte',
    }

    def __init__(self):
        super().__init__(list(self.LANGUAGE_MAP.keys()))

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.extensions

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        ext = os.path.splitext(filepath)[1].lower()
        stat = os.stat(filepath)
        return {
            "format": "code",
            "language": self.LANGUAGE_MAP.get(ext, 'unknown'),
            "size_bytes": stat.st_size,
            "extension": ext,
        }

    def get_language(self, filepath: str) -> Optional[str]:
        ext = os.path.splitext(filepath)[1].lower()
        return self.LANGUAGE_MAP.get(ext)


class JsonHandler(FormatHandler):
    """JSON文件处理器"""

    def __init__(self):
        super().__init__(['.json'])

    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith('.json')

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        try:
            data = json.loads(content)
            # 将JSON转换为可读的文本表示
            return self._json_to_text(data)
        except json.JSONDecodeError:
            return content

    def _json_to_text(self, data: Any, prefix: str = "") -> str:
        """将JSON数据转换为文本"""
        lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._json_to_text(value, prefix + "  "))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data[:50]):  # 限制列表长度
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.append(self._json_to_text(item, prefix + "  "))
                else:
                    lines.append(f"{prefix}- {item}")
            if len(data) > 50:
                lines.append(f"{prefix}... ({len(data) - 50} more items)")
        else:
            lines.append(f"{prefix}{data}")
        return '\n'.join(lines)

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        stat = os.stat(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        try:
            data = json.loads(content)
            return {
                "format": "json",
                "size_bytes": stat.st_size,
                "keys_count": len(data) if isinstance(data, dict) else 0,
                "items_count": len(data) if isinstance(data, list) else 0,
            }
        except:
            return {
                "format": "json",
                "size_bytes": stat.st_size,
                "valid": False,
            }

    def get_language(self, filepath: str = "") -> Optional[str]:
        return "json"


class YamlHandler(FormatHandler):
    """YAML文件处理器"""

    def __init__(self):
        super().__init__(['.yaml', '.yml'])

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.extensions

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        stat = os.stat(filepath)
        return {
            "format": "yaml",
            "size_bytes": stat.st_size,
            "extension": os.path.splitext(filepath)[1],
        }


class LogHandler(FormatHandler):
    """日志文件处理器"""

    def __init__(self):
        super().__init__(['.log'])

    def can_handle(self, filepath: str) -> bool:
        return filepath.lower().endswith('.log')

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        stat = os.stat(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 分析日志级别分布
        levels = {'INFO': 0, 'DEBUG': 0, 'WARN': 0, 'WARNING': 0,
                  'ERROR': 0, 'FATAL': 0, 'CRITICAL': 0}
        for line in lines:
            for level in levels:
                if level in line.upper():
                    levels[level] += 1

        return {
            "format": "log",
            "size_bytes": stat.st_size,
            "line_count": len(lines),
            "level_distribution": {k: v for k, v in levels.items() if v > 0},
        }


class ConfigHandler(FormatHandler):
    """配置文件处理器"""

    def __init__(self):
        super().__init__(['.ini', '.conf', '.cfg', '.toml', '.properties'])

    def can_handle(self, filepath: str) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in self.extensions

    def extract_text(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        stat = os.stat(filepath)
        return {
            "format": "config",
            "size_bytes": stat.st_size,
            "extension": os.path.splitext(filepath)[1],
        }


class FormatHandlerRegistry:
    """
    格式处理器注册表

    管理所有格式处理器，提供统一的文件处理接口。
    """

    def __init__(self):
        self.handlers: List[FormatHandler] = [
            TextHandler(),
            CodeHandler(),
            JsonHandler(),
            YamlHandler(),
            LogHandler(),
            ConfigHandler(),
        ]

    def get_handler(self, filepath: str) -> Optional[FormatHandler]:
        """获取能处理该文件的处理器"""
        for handler in self.handlers:
            if handler.can_handle(filepath):
                return handler
        return None

    def extract_text(self, filepath: str) -> str:
        """从文件中提取文本"""
        handler = self.get_handler(filepath)
        if handler:
            return handler.extract_text(filepath)
        # 默认按文本处理
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_metadata(self, filepath: str) -> Dict[str, Any]:
        """获取文件元数据"""
        handler = self.get_handler(filepath)
        if handler:
            return handler.get_metadata(filepath)
        return {"format": "unknown", "size_bytes": os.path.getsize(filepath)}

    def get_language(self, filepath: str) -> Optional[str]:
        """获取文件语言"""
        handler = self.get_handler(filepath)
        if handler and hasattr(handler, 'get_language'):
            if callable(getattr(handler, 'get_language')):
                return handler.get_language(filepath)
        return None

    def list_supported_formats(self) -> List[str]:
        """列出支持的格式"""
        formats = []
        for handler in self.handlers:
            formats.extend(handler.extensions)
        return sorted(formats)
