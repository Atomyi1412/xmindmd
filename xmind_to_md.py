#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind to Markdown Converter

这个工具可以将 XMind 思维导图文件转换为 Markdown 格式。
支持多级标题、列表和基本的思维导图结构。
"""

import os
import sys
import argparse
import json
from typing import Dict, List, Any, Optional

try:
    import xmindparser
except ImportError:
    print("错误: 请先安装 xmindparser 库")
    print("运行: pip install xmindparser")
    sys.exit(1)


class XMindToMarkdownConverter:
    """XMind 到 Markdown 转换器"""
    
    def __init__(self):
        self.output_lines = []
    
    def convert_file(self, xmind_file: str, output_file: Optional[str] = None) -> str:
        """
        转换 XMind 文件到 Markdown
        
        Args:
            xmind_file: XMind 文件路径
            output_file: 输出文件路径，如果为 None 则自动生成
            
        Returns:
            生成的 Markdown 内容
        """
        if not os.path.exists(xmind_file):
            raise FileNotFoundError(f"XMind 文件不存在: {xmind_file}")
        
        # 解析 XMind 文件
        try:
            content = xmindparser.xmind_to_dict(xmind_file)
        except Exception as e:
            raise Exception(f"解析 XMind 文件失败: {str(e)}")
        
        # 重置输出
        self.output_lines = []
        
        # 转换内容
        self._convert_content(content)
        
        # 生成 Markdown 内容
        markdown_content = '\n'.join(self.output_lines)
        
        # 保存到文件
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(xmind_file))[0]
            output_file = f"{base_name}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"转换完成: {xmind_file} -> {output_file}")
        return markdown_content
    
    def _convert_content(self, content: List[Dict[str, Any]]):
        """
        转换 XMind 内容到 Markdown
        
        Args:
            content: XMind 解析后的内容
        """
        for sheet in content:
            if 'topic' in sheet:
                self._convert_topic(sheet['topic'], level=1)
    
    def _convert_topic(self, topic: Dict[str, Any], level: int = 1):
        """
        转换主题到 Markdown
        
        Args:
            topic: 主题数据
            level: 标题级别
        """
        # 获取主题标题
        title = topic.get('title', '未命名主题')
        
        # 根据级别生成标题
        if level <= 6:
            # 使用 Markdown 标题格式
            header = '#' * level + ' ' + title
            self.output_lines.append(header)
        else:
            # 超过 6 级使用列表格式
            indent = '  ' * (level - 7)
            self.output_lines.append(f"{indent}- {title}")
        
        # 添加备注
        if 'note' in topic:
            note = topic['note'].strip()
            if note:
                self.output_lines.append('')
                # 将备注作为引用块
                for line in note.split('\n'):
                    self.output_lines.append(f"> {line}")
                self.output_lines.append('')
        
        # 处理子主题
        if 'topics' in topic:
            for subtopic in topic['topics']:
                self._convert_topic(subtopic, level + 1)
        
        # 在同级主题之间添加空行
        if level <= 3:
            self.output_lines.append('')
    
    def convert_to_list_format(self, xmind_file: str, output_file: Optional[str] = None) -> str:
        """
        转换 XMind 文件到列表格式的 Markdown
        
        Args:
            xmind_file: XMind 文件路径
            output_file: 输出文件路径
            
        Returns:
            生成的 Markdown 内容
        """
        if not os.path.exists(xmind_file):
            raise FileNotFoundError(f"XMind 文件不存在: {xmind_file}")
        
        try:
            content = xmindparser.xmind_to_dict(xmind_file)
        except Exception as e:
            raise Exception(f"解析 XMind 文件失败: {str(e)}")
        
        self.output_lines = []
        
        for sheet in content:
            if 'topic' in sheet:
                self._convert_topic_to_list(sheet['topic'], level=0)
        
        markdown_content = '\n'.join(self.output_lines)
        
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(xmind_file))[0]
            output_file = f"{base_name}_list.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"转换完成 (列表格式): {xmind_file} -> {output_file}")
        return markdown_content
    
    def _convert_topic_to_list(self, topic: Dict[str, Any], level: int = 0):
        """
        转换主题到列表格式
        
        Args:
            topic: 主题数据
            level: 缩进级别
        """
        title = topic.get('title', '未命名主题')
        indent = '  ' * level
        
        if level == 0:
            # 根主题使用一级标题
            self.output_lines.append(f"# {title}")
            self.output_lines.append('')
        else:
            # 子主题使用列表
            self.output_lines.append(f"{indent}- {title}")
        
        # 添加备注
        if 'note' in topic:
            note = topic['note'].strip()
            if note:
                for line in note.split('\n'):
                    self.output_lines.append(f"{indent}  > {line}")
        
        # 处理子主题
        if 'topics' in topic:
            for subtopic in topic['topics']:
                self._convert_topic_to_list(subtopic, level + 1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='将 XMind 思维导图转换为 Markdown 格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python xmind_to_md.py input.xmind                    # 转换为标题格式
  python xmind_to_md.py input.xmind -o output.md      # 指定输出文件
  python xmind_to_md.py input.xmind --list            # 转换为列表格式
  python xmind_to_md.py input.xmind --list -o list.md # 列表格式并指定输出文件
        """
    )
    
    parser.add_argument('input', help='输入的 XMind 文件路径')
    parser.add_argument('-o', '--output', help='输出的 Markdown 文件路径')
    parser.add_argument('--list', action='store_true', help='使用列表格式而不是标题格式')
    parser.add_argument('--version', action='version', version='XMind to Markdown Converter 1.0')
    
    args = parser.parse_args()
    
    try:
        converter = XMindToMarkdownConverter()
        
        if args.list:
            converter.convert_to_list_format(args.input, args.output)
        else:
            converter.convert_file(args.input, args.output)
            
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()