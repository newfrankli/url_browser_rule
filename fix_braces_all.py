#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Python文件中CSS样式表的花括号转义问题
将所有CSS块的花括号从 { } 转换为 {{ }}
"""

import re

def fix_css_braces(file_path):
    """修复文件中所有CSS样式表的花括号转义问题"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有f-string中的CSS样式表
    # 匹配模式：f"""...""" 或 f'...' 中的CSS样式
    pattern = r'(f["\']{3}.*?["\']{3}|f["\'].*?["\'])'
    
    def replace_braces(match):
        """替换匹配到的f-string中的花括号"""
        f_string = match.group(0)
        # 仅处理包含CSS样式的f-string
        if 'background-color' in f_string or 'color:' in f_string or 'border:' in f_string:
            # 替换CSS块的花括号，但保留变量插值的花括号
            # 先找到所有变量插值的位置
            var_pattern = r'\{self\.[^}]+\}|\{scaled_font_size\}|\{self\.border_thickness\}|\{self\.font_family\}|\{self\.base_font_size\}'
            
            # 保存所有变量插值
            vars_list = re.findall(var_pattern, f_string)
            
            # 临时替换变量插值为占位符
            temp_f_string = f_string
            for i, var in enumerate(vars_list):
                temp_f_string = temp_f_string.replace(var, f'__VAR{i}__')
            
            # 替换CSS花括号为双花括号
            temp_f_string = temp_f_string.replace('{', '{{').replace('}', '}}')
            
            # 恢复变量插值
            for i, var in enumerate(vars_list):
                temp_f_string = temp_f_string.replace(f'__VAR{i}__', var)
            
            return temp_f_string
        return f_string
    
    # 应用替换
    new_content = re.sub(pattern, replace_braces, content, flags=re.DOTALL)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已修复文件: {file_path}")

if __name__ == "__main__":
    # 修复主Python文件
    fix_css_braces("url_browser_rule_advanced_pyqt.py")
    print("修复完成！")
