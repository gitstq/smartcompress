<div align="center">

# 🗜️ SmartCompress

**智能文本压缩与Token优化工具**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-21%2F21%20passed-brightgreen)](tests/)

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

</div>

---

## 简体中文

### 🎉 项目介绍

**SmartCompress** 是一款专为大型语言模型（LLM）上下文窗口优化而设计的智能文本压缩工具。随着GPT-4、Claude等大模型的普及，上下文窗口的限制成为开发者和用户面临的核心痛点——当需要处理的文本超出模型容量时，要么被迫截断内容导致信息丢失，要么需要多次调用增加成本和延迟。

本项目灵感来源于GitHub Trending上的 [headroom](https://github.com/chopratejas/headroom) 项目，但我们进行了**完全独立自研开发**，在参考其产品逻辑的基础上，实现了多项差异化优化：

- 🧠 **智能策略选择** - 自动识别文本类型并选择最优压缩策略
- 📊 **精确Token计数** - 基于OpenAI tiktoken，精确计算压缩前后的token数量
- 🌊 **流式大文件处理** - 支持超大文件的分块流式压缩，内存占用极低
- 🔌 **可扩展架构** - 插件化策略设计，易于扩展新的压缩算法

### ✨ 核心特性

| 特性 | 说明 | 表情 |
|------|------|------|
| **🎯 五种压缩策略** | 摘要、关键词提取、语义去重、代码精简、智能混合 | 🧠 |
| **📏 精确Token计数** | 支持cl100k_base等多种tokenizer | 📊 |
| **📁 多格式支持** | 文本、代码、JSON、YAML、日志、配置文件等 | 📂 |
| **🌊 流式处理** | 大文件分块压缩，内存友好 | 🌊 |
| **💰 Token预算控制** | 设定最大token数，自动压缩至目标范围 | 💰 |
| **🎨 美观CLI界面** | 基于Rich库的彩色命令行交互 | 🎨 |
| **🔧 易于集成** | 既可作为命令行工具，也可作为Python库使用 | 🔧 |

### 🚀 快速开始

#### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

#### 安装步骤

```bash
# 从PyPI安装（即将发布）
pip install smartcompress

# 或从源码安装
git clone https://github.com/gitstq/smartcompress.git
cd smartcompress
pip install -e .
```

#### 基本使用

```bash
# 压缩单个文件
smartcompress compress input.txt --ratio 0.5

# 查看文件token统计
smartcompress stats input.txt

# 批量压缩目录
smartcompress batch ./logs --ratio 0.3 --output-dir ./compressed

# 流式压缩大文件
smartcompress stream large.log --chunk-size 4000 --ratio 0.5
```

#### Python API 使用

```python
from smartcompress import SmartCompressor

# 创建压缩器实例
compressor = SmartCompressor(strategy='hybrid')

# 压缩文本
text = "这是一段需要压缩的长文本..." * 100
result = compressor.compress(text, target_ratio=0.5)

print(f"原始Token: {result.original_tokens}")
print(f"压缩后Token: {result.compressed_tokens}")
print(f"压缩率: {result.reduction_ratio}%")

# 使用token预算控制
result = compressor.compress(text, max_tokens=1000)
```

### 📖 详细使用指南

#### 压缩策略说明

| 策略 | 适用场景 | 压缩方式 |
|------|----------|----------|
| `summarize` | 文章、报告、长文本 | 提取关键段落，去除冗余内容 |
| `keyword` | 笔记、会议纪要、文档 | 提取关键词和关键短语 |
| `dedup` | 日志、聊天记录、重复文本 | 语义去重，合并相似内容 |
| `code` | 源代码、配置文件 | 去除注释和空行，保留核心逻辑 |
| `hybrid` | 通用场景（**推荐**） | 自动识别文本类型并组合策略 |

#### 命令行参数详解

```bash
# 压缩命令
smartcompress compress <文件路径> [选项]
  -s, --strategy    压缩策略 (summarize/keyword/dedup/code/hybrid)
  -r, --ratio       目标压缩率 (0-1)
  -m, --max-tokens  最大token限制
  -o, --output      输出文件路径
  --model           Tokenizer模型 (默认: cl100k_base)
  -l, --language    代码语言（用于代码压缩）

# 统计命令
smartcompress stats <文件路径>
  --model           Tokenizer模型

# 批量压缩
smartcompress batch <目录路径> [选项]
  -p, --pattern     文件匹配模式 (默认: *)
  --recursive       递归处理子目录
  -o, --output-dir  输出目录

# 流式压缩
smartcompress stream <文件路径> [选项]
  -c, --chunk-size  每块token数 (默认: 4000)
```

### 💡 设计思路与迭代规划

#### 技术选型原因

- **Python 3.8+**: 兼顾语法特性与兼容性
- **tiktoken**: OpenAI官方tokenizer，精确计算GPT系列模型的token数
- **Click**: 成熟的Python CLI框架，支持丰富的命令行交互
- **Rich**: 提供美观的终端输出，包括表格、进度条、面板等

#### 后续功能迭代计划

- [ ] 支持更多tokenizer（HuggingFace Tokenizers、SentencePiece等）
- [ ] 增加基于LLM的智能摘要策略
- [ ] 支持压缩质量评估与对比
- [ ] Web UI界面
- [ ] 支持更多文件格式（PDF、Word、Excel等）

### 📦 打包与部署指南

#### 本地开发

```bash
# 克隆仓库
git clone https://github.com/gitstq/smartcompress.git
cd smartcompress

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v
```

#### 打包发布

```bash
# 构建分发包
python setup.py sdist bdist_wheel

# 上传到PyPI
twine upload dist/*
```

### 🤝 贡献指南

欢迎提交Issue和Pull Request！

- **Bug报告**: 请提供复现步骤和错误日志
- **功能建议**: 请描述使用场景和预期行为
- **代码贡献**: 请遵循PEP 8规范，并确保测试通过

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 繁體中文

### 🎉 專案介紹

**SmartCompress** 是一款專為大型語言模型（LLM）上下文視窗優化而設計的智慧文字壓縮工具。隨著 GPT-4、Claude 等大模型的普及，上下文視窗的限制成為開發者和使用者面臨的核心痛點。

本專案靈感來源於 GitHub Trending 上的 headroom 專案，但我們進行了**完全獨立自研開發**，在參考其產品邏輯的基礎上，實現了多項差異化優化。

### ✨ 核心特性

- 🧠 **五種壓縮策略** - 摘要、關鍵詞提取、語義去重、程式碼精簡、智慧混合
- 📊 **精確 Token 計數** - 支援 cl100k_base 等多種 tokenizer
- 📁 **多格式支援** - 文字、程式碼、JSON、YAML、日誌、設定檔等
- 🌊 **流式處理** - 大檔案分塊壓縮，記憶體友好
- 💰 **Token 預算控制** - 設定最大 token 數，自動壓縮至目標範圍

### 🚀 快速開始

#### 安裝

```bash
pip install smartcompress
```

#### 基本使用

```bash
# 壓縮單個檔案
smartcompress compress input.txt --ratio 0.5

# 查看檔案 token 統計
smartcompress stats input.txt

# 批次壓縮目錄
smartcompress batch ./logs --ratio 0.3 --output-dir ./compressed
```

#### Python API

```python
from smartcompress import SmartCompressor

compressor = SmartCompressor(strategy='hybrid')
result = compressor.compress(text, target_ratio=0.5)
print(f"壓縮率: {result.reduction_ratio}%")
```

### 📖 詳細使用指南

#### 壓縮策略說明

| 策略 | 適用場景 | 壓縮方式 |
|------|----------|----------|
| `summarize` | 文章、報告、長文本 | 提取關鍵段落 |
| `keyword` | 筆記、會議紀要 | 提取關鍵詞和關鍵短語 |
| `dedup` | 日誌、聊天記錄 | 語義去重 |
| `code` | 原始碼、設定檔 | 去除註解和空行 |
| `hybrid` | 通用場景（**推薦**） | 自動識別並組合策略 |

### 💡 設計思路與迭代規劃

#### 技術選型原因

- **Python 3.8+**: 兼顧語法特性與相容性
- **tiktoken**: OpenAI 官方 tokenizer
- **Click**: 成熟的 Python CLI 框架
- **Rich**: 提供美觀的終端輸出

#### 後續功能迭代計劃

- [ ] 支援更多 tokenizer
- [ ] 增加基於 LLM 的智慧摘要策略
- [ ] Web UI 介面
- [ ] 支援更多檔案格式（PDF、Word 等）

### 📦 打包與部署指南

```bash
# 本地開發
git clone https://github.com/gitstq/smartcompress.git
cd smartcompress
pip install -e .
pytest tests/ -v
```

### 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 📄 開源協議

本專案採用 [MIT License](LICENSE) 開源協議。

---

## English

### 🎉 Project Introduction

**SmartCompress** is an intelligent text compression tool designed for Large Language Model (LLM) context window optimization. As GPT-4, Claude, and other large models become prevalent, context window limitations have become a core pain point for developers and users.

Inspired by the [headroom](https://github.com/chopratejas/headroom) project on GitHub Trending, we have developed this project **completely independently** with several differentiated optimizations.

### ✨ Core Features

- 🧠 **Five Compression Strategies** - Summarize, Keyword Extract, Semantic Deduplicate, Code Minify, Smart Hybrid
- 📊 **Accurate Token Counting** - Supports cl100k_base and other tokenizers
- 📁 **Multi-format Support** - Text, Code, JSON, YAML, Logs, Config files
- 🌊 **Streaming Processing** - Chunk-based compression for large files, memory-friendly
- 💰 **Token Budget Control** - Set max token limit, auto-compress to target range

### 🚀 Quick Start

#### Installation

```bash
pip install smartcompress
```

#### Basic Usage

```bash
# Compress a single file
smartcompress compress input.txt --ratio 0.5

# View file token statistics
smartcompress stats input.txt

# Batch compress directory
smartcompress batch ./logs --ratio 0.3 --output-dir ./compressed
```

#### Python API

```python
from smartcompress import SmartCompressor

compressor = SmartCompressor(strategy='hybrid')
result = compressor.compress(text, target_ratio=0.5)
print(f"Reduction: {result.reduction_ratio}%")
```

### 📖 Detailed Usage Guide

#### Compression Strategies

| Strategy | Use Case | Method |
|----------|----------|--------|
| `summarize` | Articles, Reports, Long text | Extract key paragraphs |
| `keyword` | Notes, Meeting minutes | Extract keywords and phrases |
| `dedup` | Logs, Chat records | Semantic deduplication |
| `code` | Source code, Config files | Remove comments and empty lines |
| `hybrid` | General use (**Recommended**) | Auto-detect and combine strategies |

### 💡 Design Philosophy & Roadmap

#### Tech Stack Rationale

- **Python 3.8+**: Balance of modern features and compatibility
- **tiktoken**: Official OpenAI tokenizer
- **Click**: Mature Python CLI framework
- **Rich**: Beautiful terminal output

#### Future Roadmap

- [ ] Support for more tokenizers
- [ ] LLM-based intelligent summarization
- [ ] Web UI interface
- [ ] Support for more file formats (PDF, Word, etc.)

### 📦 Packaging & Deployment

```bash
# Local development
git clone https://github.com/gitstq/smartcompress.git
cd smartcompress
pip install -e .
pytest tests/ -v
```

### 🤝 Contributing

Issues and Pull Requests are welcome!

### 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made with ❤️ by SmartCompress Team

</div>
