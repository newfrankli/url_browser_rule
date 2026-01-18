# 修复样式字符串中的大括号转义问题
import os

# 读取原始文件
with open('url_browser_rule_advanced_pyqt.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有CSS样式字符串中的大括号
# 注意：这种方法可能需要根据实际情况调整
# 我们将匹配CSS样式块并转义其中的大括号

# 修复setup_ui方法中的输入框样式
content = content.replace(
    "        self.url_input.setStyleSheet(f\"\"\"
            QLineEdit {
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {self.base_font_size}px;
                padding: 2px;
                selection-background-color: white;
                selection-color: black;
                background-clip: padding;
                border-radius: 0;
            }
            QLineEdit:focus {
                outline: none;
                border-color: white;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.8);
            }
        \"\"")",
    "        self.url_input.setStyleSheet(f\"\"\"
            QLineEdit {{
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {self.base_font_size}px;
                padding: 2px;
                selection-background-color: white;
                selection-color: black;
                background-clip: padding;
                border-radius: 0;
            }}
            QLineEdit:focus {{
                outline: none;
                border-color: white;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.8);
            }}
        \"\"")"
)

# 修复setup_ui方法中的冒号标签样式
content = content.replace(
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {
                color: white;
                font-family: {self.font_family};
                font-size: {self.base_font_size * 2}px;
                font-weight: bold;
                background-color: transparent;
            }
        \"\"")",
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {{
                color: white;
                font-family: {self.font_family};
                font-size: {self.base_font_size * 2}px;
                font-weight: bold;
                background-color: transparent;
            }}
        \"\"")"
)

# 修复setup_ui方法中的访问按钮样式
content = content.replace(
    "        self.visit_btn.setStyleSheet(f\"\"\"
            QPushButton {
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {self.base_font_size}px;
                font-weight: bold;
                background-clip: padding;
                border-radius: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:focus {
                outline: none;
                border-color: white;
            }
        \"\"")",
    "        self.visit_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {self.base_font_size}px;
                font-weight: bold;
                background-clip: padding;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:focus {{
                outline: none;
                border-color: white;
            }}
        \"\"")"
)

# 修复resize_widgets方法中的输入框样式
content = content.replace(
    "        self.url_input.setStyleSheet(f\"\"\"
            QLineEdit {
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {scaled_font_size}px;
                padding: 2px;
                selection-background-color: white;
                selection-color: black;
                background-clip: padding;
                border-radius: 0;
            }
            QLineEdit:focus {
                outline: none;
                border-color: white;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.8);
            }
        \"\"")",
    "        self.url_input.setStyleSheet(f\"\"\"
            QLineEdit {{
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {scaled_font_size}px;
                padding: 2px;
                selection-background-color: white;
                selection-color: black;
                background-clip: padding;
                border-radius: 0;
            }}
            QLineEdit:focus {{
                outline: none;
                border-color: white;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.8);
            }}
        \"\"")"
)

# 修复resize_widgets方法中的冒号标签样式
content = content.replace(
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {
                color: white;
                font-family: {self.font_family};
                font-size: {scaled_font_size * 2}px;
                font-weight: bold;
                background-color: transparent;
            }
        \"\"")",
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {{
                color: white;
                font-family: {self.font_family};
                font-size: {scaled_font_size * 2}px;
                font-weight: bold;
                background-color: transparent;
            }}
        \"\"")"
)

# 修复resize_widgets方法中的访问按钮样式
content = content.replace(
    "        self.visit_btn.setStyleSheet(f\"\"\"
            QPushButton {
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {scaled_font_size}px;
                font-weight: bold;
                background-clip: padding;
                border-radius: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:focus {
                outline: none;
                border-color: white;
            }
        \"\"")",
    "        self.visit_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: transparent;
                color: white;
                border: {self.border_thickness}px solid white;
                font-family: {self.font_family};
                font-size: {scaled_font_size}px;
                font-weight: bold;
                background-clip: padding;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:focus {{
                outline: none;
                border-color: white;
            }}
        \"\"")"
)

# 保存修复后的文件
with open('url_browser_rule_advanced_pyqt.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
