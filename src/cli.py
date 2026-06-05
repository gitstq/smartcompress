"""
命令行接口模块 - 提供友好的CLI交互

命令:
    smartcompress compress <file>    压缩文件
    smartcompress stats <file>       查看Token统计
    smartcompress batch <dir>        批量压缩目录
    smartcompress stream <file>      流式压缩大文件
"""

import os
import sys
import json
from typing import Optional
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from .compressor import SmartCompressor
from .token_counter import TokenCounter


console = Console()


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗ ██████╗     ║
║   ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██╔════╝     ║
║   ███████╗██╔████╔██║███████║██████╔╝   ██║   ██║          ║
║   ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██║          ║
║   ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ╚██████╗     ║
║   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝     ║
║                                                              ║
║        智能文本压缩与Token优化工具 v1.0.0                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="cyan")


@click.group()
@click.version_option(version="1.0.0", prog_name="smartcompress")
def main():
    """SmartCompress - 智能文本压缩与Token优化工具"""
    pass


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--strategy', '-s', default='hybrid',
              type=click.Choice(['summarize', 'keyword', 'dedup', 'code', 'hybrid']),
              help='压缩策略')
@click.option('--ratio', '-r', default=0.5, type=float,
              help='目标压缩率 (0-1)', show_default=True)
@click.option('--max-tokens', '-m', type=int,
              help='最大Token限制（优先于压缩率）')
@click.option('--output', '-o', type=click.Path(),
              help='输出文件路径')
@click.option('--model', default='cl100k_base',
              help='Tokenizer模型', show_default=True)
@click.option('--language', '-l',
              help='代码语言（用于代码压缩策略）')
def compress(input_path, strategy, ratio, max_tokens, output, model, language):
    """压缩文件或文本"""
    print_banner()

    compressor = SmartCompressor(strategy=strategy, model=model)

    # 检查是否是文件
    if os.path.isfile(input_path):
        console.print(f"📄 正在压缩文件: [bold]{input_path}[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在分析并压缩...", total=None)

            kwargs = {}
            if language:
                kwargs['language'] = language

            result = compressor.compress_file(
                input_path,
                target_ratio=ratio,
                max_tokens=max_tokens,
                output_path=output,
                **kwargs
            )

            progress.update(task, completed=True)

        # 显示结果
        _display_result(result)

        if output:
            console.print(f"\n✅ 结果已保存到: [bold green]{output}[/bold green]")

    else:
        console.print("❌ 输入路径不存在", style="red")


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--model', default='cl100k_base', help='Tokenizer模型')
def stats(input_path, model):
    """查看文件的Token统计信息"""
    print_banner()

    counter = TokenCounter(model)

    if os.path.isfile(input_path):
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        file_stats = counter.get_stats(content)
        file_size = os.path.getsize(input_path)

        # 创建统计表格
        table = Table(title="📊 Token统计信息", show_header=True, header_style="bold magenta")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="green")

        table.add_row("文件路径", input_path)
        table.add_row("文件大小", f"{file_size:,} bytes ({_format_size(file_size)})")
        table.add_row("字符数", f"{file_stats['char_count']:,}")
        table.add_row("Token数", f"{file_stats['token_count']:,}")
        table.add_row("字符/Token比", str(file_stats['chars_per_token']))
        table.add_row("Tokenizer模型", file_stats['model'])

        console.print(table)

        # 预估不同压缩率的效果
        console.print("\n📈 预估压缩效果:")
        estimate_table = Table(show_header=True, header_style="bold blue")
        estimate_table.add_column("目标压缩率", style="cyan")
        estimate_table.add_column("预估Token数", style="green")
        estimate_table.add_column("预估节省", style="yellow")

        for r in [0.9, 0.7, 0.5, 0.3, 0.1]:
            est = compressor.estimate_compression(content, r) if 'compressor' in locals() else None
            if not est:
                compressor = SmartCompressor(model=model)
                est = compressor.estimate_compression(content, r)
            estimate_table.add_row(
                f"{r*100:.0f}%",
                f"{est['estimated_tokens']:,}",
                est['estimated_reduction']
            )

        console.print(estimate_table)

    else:
        console.print("❌ 文件不存在", style="red")


@main.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--strategy', '-s', default='hybrid',
              type=click.Choice(['summarize', 'keyword', 'dedup', 'code', 'hybrid']))
@click.option('--ratio', '-r', default=0.5, type=float)
@click.option('--output-dir', '-o', type=click.Path(), help='输出目录')
@click.option('--pattern', '-p', default='*', help='文件匹配模式')
@click.option('--recursive/--no-recursive', default=True, help='递归处理子目录')
def batch(input_dir, strategy, ratio, output_dir, pattern, recursive):
    """批量压缩目录中的文件"""
    print_banner()

    compressor = SmartCompressor(strategy=strategy)

    # 收集文件
    import glob
    if recursive:
        search_pattern = os.path.join(input_dir, '**', pattern)
    else:
        search_pattern = os.path.join(input_dir, pattern)

    files = [f for f in glob.glob(search_pattern, recursive=recursive) if os.path.isfile(f)]

    if not files:
        console.print(f"❌ 未找到匹配的文件: {pattern}", style="red")
        return

    console.print(f"📁 找到 {len(files)} 个文件，开始批量压缩...\n")

    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 批量压缩
    results = compressor.compress_batch(files, target_ratio=ratio, output_dir=output_dir)

    # 显示结果
    table = Table(title="📋 批量压缩结果", show_header=True, header_style="bold magenta")
    table.add_column("文件", style="cyan")
    table.add_column("原始Token", justify="right", style="green")
    table.add_column("压缩后", justify="right", style="blue")
    table.add_column("压缩率", justify="right", style="yellow")

    total_original = 0
    total_compressed = 0

    for filepath, result in zip(files, results):
        filename = os.path.basename(filepath)
        total_original += result.original_tokens
        total_compressed += result.compressed_tokens

        if result.reduction_ratio > 0:
            table.add_row(
                filename,
                f"{result.original_tokens:,}",
                f"{result.compressed_tokens:,}",
                f"{result.reduction_ratio}%"
            )
        else:
            table.add_row(filename, "-", "-", "错误/跳过", style="dim")

    console.print(table)

    # 总计
    if total_original > 0:
        total_ratio = round((total_original - total_compressed) / total_original * 100, 2)
        console.print(f"\n📊 总计: {total_original:,} → {total_compressed:,} tokens "
                     f"(节省 {total_ratio}%)", style="bold green")


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--chunk-size', '-c', default=4000, type=int, help='每块Token数')
@click.option('--strategy', '-s', default='hybrid',
              type=click.Choice(['summarize', 'keyword', 'dedup', 'code', 'hybrid']))
@click.option('--ratio', '-r', default=0.5, type=float)
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
def stream(input_path, chunk_size, strategy, ratio, output):
    """流式压缩大文件"""
    print_banner()

    compressor = SmartCompressor(strategy=strategy)

    console.print(f"🌊 流式压缩: [bold]{input_path}[/bold]")
    console.print(f"   块大小: {chunk_size} tokens\n")

    results = compressor.stream_compress(
        input_path,
        chunk_size=chunk_size,
        target_ratio=ratio,
        callback=lambda r: console.print(f"   ✓ 块压缩完成: {r.original_tokens} → {r.compressed_tokens} tokens")
    )

    # 合并结果
    total_original = sum(r.original_tokens for r in results)
    total_compressed = sum(r.compressed_tokens for r in results)

    console.print(f"\n📊 流式压缩完成:")
    console.print(f"   总块数: {len(results)}")
    console.print(f"   原始Token: {total_original:,}")
    console.print(f"   压缩后: {total_compressed:,}")
    if total_original > 0:
        ratio_pct = round((total_original - total_compressed) / total_original * 100, 2)
        console.print(f"   压缩率: {ratio_pct}%", style="bold green")

    # 保存结果
    if output:
        combined = '\n\n'.join(r.compressed_text for r in results)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(combined)
        console.print(f"\n✅ 结果已保存到: [bold green]{output}[/bold green]")


def _display_result(result):
    """显示压缩结果"""
    # 结果表格
    table = Table(title="📋 压缩结果", show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")

    table.add_row("压缩策略", result.strategy_name)
    table.add_row("原始Token", f"{result.original_tokens:,}")
    table.add_row("压缩后Token", f"{result.compressed_tokens:,}")
    table.add_row("压缩率", f"[bold yellow]{result.reduction_ratio}%[/bold yellow]")
    table.add_row("节省Token", f"{result.original_tokens - result.compressed_tokens:,}")

    if result.metadata:
        for key, value in result.metadata.items():
            if key != 'file_info':
                table.add_row(str(key), str(value)[:100])

    console.print(table)

    # 显示压缩后内容预览
    if result.compressed_text:
        preview = result.compressed_text[:500]
        if len(result.compressed_text) > 500:
            preview += "\n... (内容已截断)"

        console.print("\n📝 压缩后内容预览:")
        console.print(Panel(preview, border_style="blue", expand=False))


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == '__main__':
    main()
