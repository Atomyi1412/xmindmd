#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to XMind Converter

这个工具可以将 Markdown 文件转换为 XMind 思维导图格式。
支持多级标题和列表结构。
"""

import os
import re
import json
import tempfile
from typing import Dict, List, Any, Optional

# 不再依赖第三方 xmind SDK。改为直接生成 XMind 2020+ 采用的 JSON 打包格式。


class MarkdownToXMindConverter:
    """Markdown 到 XMind 转换器"""
    
    def __init__(self):
        pass
    
    def convert_file(self, md_file: str, output_file: Optional[str] = None) -> str:
        """
        转换 Markdown 文件到 XMind
        
        Args:
            md_file: Markdown 文件路径
            output_file: 输出文件路径，如果为 None 则自动生成
            
        Returns:
            输出文件路径
        """
        if not os.path.exists(md_file):
            raise FileNotFoundError(f"Markdown 文件不存在: {md_file}")
        
        # 读取 Markdown 文件
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 Markdown 内容
        structure = self._parse_markdown(content)
        
        # 生成输出文件名
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(md_file))[0]
            output_file = f"{base_name}.xmind"
        
        # 创建 XMind 文件（JSON 打包格式）
        self._create_xmind(structure, output_file)
        
        print(f"转换完成: {md_file} -> {output_file}")
        return output_file
    
    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """
        解析 Markdown 内容
        
        Args:
            content: Markdown 内容
            
        Returns:
            解析后的结构
        """
        lines = content.split('\n')
        structure = {
            'title': 'Markdown 思维导图',
            'children': []
        }
        
        current_path = [structure]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # 创建新节点
                node = {
                    'title': title,
                    'children': []
                }
                
                # 调整路径到正确的层级
                while len(current_path) > level:
                    current_path.pop()
                
                # 添加到父节点
                if len(current_path) == 0:
                    current_path = [structure]
                
                current_path[-1]['children'].append(node)
                current_path.append(node)
                
                # 如果是一级标题且是第一个，设为根标题
                if level == 1 and len(structure['children']) == 1:
                    structure['title'] = title
                
                continue
            
            # 处理列表项
            list_match = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
            if list_match:
                indent = len(list_match.group(1))
                title = list_match.group(3).strip()
                level = (indent // 2) + 1  # 每两个空格为一级
                
                # 创建新节点
                node = {
                    'title': title,
                    'children': []
                }
                
                # 调整路径到正确的层级
                while len(current_path) > level + 1:
                    current_path.pop()
                
                # 确保有足够的层级
                if len(current_path) == 0:
                    current_path = [structure]
                
                current_path[-1]['children'].append(node)
                current_path.append(node)
                
                continue
            
            # 处理普通文本（作为备注或子节点）
            if line and len(current_path) > 1:
                # 如果当前节点没有子节点，将文本作为备注
                current_node = current_path[-1]
                if not current_node['children']:
                    if 'note' not in current_node:
                        current_node['note'] = line
                    else:
                        current_node['note'] += '\n' + line
                else:
                    # 否则作为子节点
                    text_node = {
                        'title': line,
                        'children': []
                    }
                    current_node['children'].append(text_node)
        
        return structure
    
    def _create_xmind(self, structure: Dict[str, Any], output_file: str):
        """
        创建 XMind 文件（JSON 打包：content.json、metadata.json、manifest.json）
        """
        import uuid
        import zipfile
        
        def uid():
            return uuid.uuid4().hex  # 任意唯一ID
        
        def build_topic(node: Dict[str, Any]) -> Dict[str, Any]:
            topic = {
                'id': uid(),
                'class': 'topic',
                'title': node.get('title', '')
            }
            # 备注（按新格式写入 plain 文本）
            if 'note' in node:
                topic['notes'] = {
                    'plain': {
                        'content': node['note']
                    }
                }
            children = [build_topic(ch) for ch in node.get('children', [])]
            if children:
                topic['children'] = {
                    'attached': children
                }
            return topic
        
        # 根主题
        root = build_topic({'title': structure.get('title', '思维导图'), 'children': structure.get('children', [])})
        
        # 单个 sheet
        sheet = {
            'id': uid(),
            'class': 'sheet',
            'title': structure.get('title', '思维导图'),
            'rootTopic': root
        }
        
        content = [sheet]
        metadata = {
            'dataStructureVersion': '2',
            'creator': {
                'name': 'XMindConverter',
                'version': '1.0'
            },
            'layoutEngineVersion': '3',
            'familyId': f'local-{uid()}'
        }
        manifest = {
            'file-entries': {
                'content.json': {},
                'metadata.json': {}
            }
        }
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        # 打包写入
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('content.json', json.dumps(content, ensure_ascii=False, separators=(',', ':')))
            z.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, separators=(',', ':')))
            z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
    
    def _add_topics(self, parent_topic, children: List[Dict[str, Any]]):
        """
        递归添加主题（旧 XML 方式的占位，保留不再使用）
        """
        pass


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='将 Markdown 文件转换为 XMind 思维导图')
    parser.add_argument('input_file', help='输入的 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出的 XMind 文件路径')
    
    args = parser.parse_args()
    
    try:
        converter = MarkdownToXMindConverter()
        output_file = converter.convert_file(args.input_file, args.output)
        print(f"转换成功！输出文件: {output_file}")
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())