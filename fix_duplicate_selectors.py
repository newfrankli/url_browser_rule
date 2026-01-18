# 修复CSS样式字符串中重复的选择器

with open('url_browser_rule_advanced_pyqt.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复重复的选择器
# 输入框样式
content = content.replace(
    "        self.url_input.setStyleSheet(f\"\"\"
            QLineEdit {
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
            QLineEdit {{\n                background-color: transparent;\n                color: white;\n                border: {self.border_thickness}px solid white;\n                font-family: {self.font_family};\n                font-size: {self.base_font_size}px;\n                padding: 2px;\n                selection-background-color: white;\n                selection-color: black;\n                background-clip: padding;\n                border-radius: 0;\n            }}\n            QLineEdit:focus {{\n                outline: none;\n                border-color: white;\n            }}\n            QLineEdit::placeholder {{\n                color: rgba(255, 255, 255, 0.8);\n            }}\n        \"\"")"
)

# 冒号标签样式
content = content.replace(
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {
            QLabel {
                color: white;
                font-family: {self.font_family};
                font-size: {self.base_font_size * 2}px;
                font-weight: bold;
                background-color: transparent;
            }
        \"\"")",
    "        self.colon_label.setStyleSheet(f\"\"\"
            QLabel {{\n                color: white;\n                font-family: {self.font_family};\n                font-size: {self.base_font_size * 2}px;\n                font-weight: bold;\n                background-color: transparent;\n            }}\n        \"\"")"
)

# 访问按钮样式
content = content.replace(
    "        self.visit_btn.setStyleSheet(f\"\"\"
            QPushButton {
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
            QPushButton {{\n                background-color: transparent;\n                color: white;\n                border: {self.border_thickness}px solid white;\n                font-family: {self.font_family};\n                font-size: {self.base_font_size}px;\n                font-weight: bold;\n                background-clip: padding;\n                border-radius: 0;\n            }}\n            QPushButton:hover {{\n                background-color: rgba(255, 255, 255, 0.1);\n            }}\n            QPushButton:focus {{\n                outline: none;\n                border-color: white;\n            }}\n        \"\"")"
)

# 保存修复后的文件
with open('url_browser_rule_advanced_pyqt.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
