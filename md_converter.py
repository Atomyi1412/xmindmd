#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown转换工具
功能：在每个三级标题(###)前添加对应的二级标题(##)
作者：AI Assistant
版本：1.0
"""

import re
import os
import sys
from typing import List, Tuple


class MarkdownConverter:
    """Markdown转换器类"""
    
    def __init__(self):
        self.content = ""
        self.converted_content = ""
    
    def read_file(self, file_path: str) -> bool:
        """读取Markdown文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 读取成功返回True，失败返回False
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            return False
        except Exception as e:
            print(f"错误：读取文件时发生异常 - {e}")
            return False
    
    def parse_headers(self) -> List[Tuple[int, str, str]]:
        """解析标题结构
        
        Returns:
            List[Tuple[int, str, str]]: 包含(行号, 标题级别, 标题内容)的列表
        """
        lines = self.content.split('\n')
        headers = []
        
        for i, line in enumerate(lines):
            # 匹配标题行
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))  # 标题级别
                title = match.group(2).strip()  # 标题内容
                headers.append((i, level, title))
        
        return headers
    
    def find_parent_h2(self, headers: List[Tuple[int, str, str]], h3_index: int) -> str:
        """查找三级标题对应的二级标题
        
        Args:
            headers: 标题列表
            h3_index: 三级标题在headers中的索引
            
        Returns:
            str: 对应的二级标题内容
        """
        # 向前查找最近的二级标题
        for i in range(h3_index - 1, -1, -1):
            if headers[i][1] == 2:  # 找到二级标题
                return headers[i][2]
        
        # 如果没找到二级标题，返回默认值
        return "未分类"
    
    def convert(self) -> str:
        """执行转换
        
        Returns:
            str: 转换后的内容
        """
        if not self.content:
            return ""
        
        lines = self.content.split('\n')
        headers = self.parse_headers()
        result_lines = []
        
        for i, line in enumerate(lines):
            # 检查当前行是否是二级标题
            is_h2 = False
            # 检查当前行是否是三级标题
            is_h3 = False
            h3_title = ""
            parent_h2 = ""
            
            for j, (line_num, level, title) in enumerate(headers):
                if line_num == i:
                    if level == 2:
                        is_h2 = True
                    elif level == 3:
                        is_h3 = True
                        h3_title = title
                        parent_h2 = self.find_parent_h2(headers, j)
                    break
            
            if is_h2:
                # 跳过原有的二级标题，因为我们会为每个三级标题重新生成
                continue
            elif is_h3:
                # 在三级标题前添加对应的二级标题
                result_lines.append(f"## {parent_h2}")
                result_lines.append(line)
            else:
                result_lines.append(line)
        
        self.converted_content = '\n'.join(result_lines)
        return self.converted_content
    
    def save_file(self, output_path: str) -> bool:
        """保存转换后的文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:  # 只有当目录不为空时才创建
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.converted_content)
            return True
        except Exception as e:
            print(f"错误：保存文件时发生异常 - {e}")
            return False
    
    def get_statistics(self) -> dict:
        """获取转换统计信息
        
        Returns:
            dict: 包含统计信息的字典
        """
        headers = self.parse_headers()
        h1_count = sum(1 for _, level, _ in headers if level == 1)
        h2_count = sum(1 for _, level, _ in headers if level == 2)
        h3_count = sum(1 for _, level, _ in headers if level == 3)
        
        return {
            'total_lines': len(self.content.split('\n')),
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'converted_h2_count': h2_count + h3_count  # 转换后的二级标题数量
        }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python md_converter.py <输入文件> [输出文件]")
        print("示例: python md_converter.py input.md output.md")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 如果没有指定输出文件，自动生成
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}（转换版）.md"
    
    # 创建转换器实例
    converter = MarkdownConverter()
    
    # 读取文件
    print(f"正在读取文件: {input_file}")
    if not converter.read_file(input_file):
        sys.exit(1)
    
    # 执行转换
    print("正在执行转换...")
    converter.convert()
    
    # 保存文件
    print(f"正在保存文件: {output_file}")
    if not converter.save_file(output_file):
        sys.exit(1)
    
    # 显示统计信息
    stats = converter.get_statistics()
    print("\n转换完成！")
    print(f"总行数: {stats['total_lines']}")
    print(f"一级标题数量: {stats['h1_count']}")
    print(f"原二级标题数量: {stats['h2_count']}")
    print(f"三级标题数量: {stats['h3_count']}")
    print(f"转换后二级标题数量: {stats['converted_h2_count']}")
    print(f"输出文件: {output_file}")


if __name__ == "__main__":
    main()