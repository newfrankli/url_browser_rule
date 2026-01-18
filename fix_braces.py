# 修复样式字符串中的大括号转义问题
# 使用更简单的方法：直接读取文件并修复

with open('url_browser_rule_advanced_pyqt.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []

for line in lines:
    # 检查是否在样式字符串中
    if 'setStyleSheet(f' in line:
        # 开始收集样式块
        style_block = [line]
        brace_count = 0
        for i in range(lines.index(line) + 1, len(lines)):
            next_line = lines[i]
            style_block.append(next_line)
            # 计算大括号数量
            brace_count += next_line.count('{') + next_line.count('}')
            # 当大括号数量匹配时，结束样式块
            if brace_count > 0 and brace_count % 2 == 0:
                break
        
        # 修复样式块中的大括号
        fixed_style = []
        for style_line in style_block:
            if 'setStyleSheet(f' in style_line:
                fixed_style.append(style_line)
            else:
                # 转义CSS中的大括号，但保留f-string中的表达式
                new_line = style_line
                # 找到所有的大括号对
                while '{' in new_line and '}' in new_line:
                    open_idx = new_line.find('{')
                    close_idx = new_line.find('}')
                    # 检查是否是f-string表达式（前面有{和空格/字母）
                    if open_idx > 0 and new_line[open_idx-1] in ' {\n\t':
                        # 这是CSS大括号，需要转义
                        new_line = new_line[:open_idx] + '{{' + new_line[open_idx+1:close_idx] + '}}' + new_line[close_idx+1:]
                    else:
                        # 这是f-string表达式，保持不变
                        break
                fixed_style.append(new_line)
        
        # 添加修复后的样式块
        fixed_lines.extend(fixed_style)
    else:
        fixed_lines.append(line)

# 保存修复后的文件
with open('url_browser_rule_advanced_pyqt.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("修复完成！")
