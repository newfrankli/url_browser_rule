import sys
import os
import json
import subprocess
import winreg
from urllib.parse import urlparse
import time
import ctypes
import shutil
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, 
    QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QTreeWidget, 
    QTreeWidgetItem, QMenu, QAction, QInputDialog, QMessageBox,
    QTabWidget, QFrame, QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
    QSystemTrayIcon, QDialogButtonBox, QFormLayout, QDialog
)
from PyQt5.QtGui import (
    QIcon, QPainter, QPen, QColor, QFont, QBrush,
    QCursor, QFontDatabase, QPixmap
)
from PyQt5.QtCore import (
    Qt, QPoint, QSize, QRect, QTimer, QEventLoop,
    QThread, pyqtSignal, QUrl
)

# 依赖说明：
# 本程序依赖PyQt5库
# 安装命令：pip install PyQt5

# 配置文件路径
RULES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
ICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'url.ico')

# 配置管理器类
class ConfigManager:
    """负责配置文件和规则文件的读写管理"""
    
    # 默认规则
    DEFAULT_RULES = [
        {
            "id": 1,
            "pattern": "google.com",
            "browser": "chrome",
            "description": "Google使用Chrome"
        },
        {
            "id": 2,
            "pattern": "bing.com",
            "browser": "firefox",
            "description": "Bing使用Firefox"
        },
        {
            "id": 3,
            "pattern": "edge.microsoft.com",
            "browser": "edge",
            "description": "Edge官网使用Edge"
        }
    ]
    
    # 默认配置
    DEFAULT_CONFIG = {
        "auto_start": False,
        "lock_position": False,
        "lock_size": False,
        "lock_ratio": True,
        "window_x": 100,
        "window_y": 100,
        "window_width": 500,
        "window_height": 100,
        "font_size": 12,
        "font_family": "Arial",
        "opacity": 0.8,
        "border_thickness": 2,
        "scale_factor": 1.0
    }
    
    def __init__(self):
        self.rules_file = RULES_FILE
        self.config_file = CONFIG_FILE
        self.default_rules = self.DEFAULT_RULES
        self.default_config = self.DEFAULT_CONFIG
    
    def read_config(self):
        """从文件读取配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # 保存默认配置
            self.save_config(self.default_config)
            return self.default_config
        except Exception as e:
            print(f"读取配置失败: {e}")
            return self.default_config
    
    def save_config(self, config):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def read_rules(self):
        """从文件读取规则"""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # 保存默认规则
            self.save_rules(self.default_rules)
            return self.default_rules
        except Exception as e:
            print(f"读取规则失败: {e}")
            return self.default_rules
    
    def save_rules(self, rules):
        """保存规则到文件"""
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存规则失败: {e}")
            return False
    
    def get_next_rule_id(self, rules):
        """获取下一个可用的规则ID"""
        if not rules:
            return 1
        return max(rule["id"] for rule in rules) + 1

# 路由引擎类
class RouterEngine:
    """负责浏览器路径扫描、URL解析和规则匹配逻辑"""
    
    # 浏览器可执行文件映射
    BROWSER_PATHS = {
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "safari": "safari.exe",
        "default": None
    }
    
    def __init__(self):
        self.browser_paths = self.BROWSER_PATHS
        self.browser_path_cache = {}
    
    def find_browser_path(self, browser_name):
        """查找浏览器的完整路径，优先使用注册表查找，然后使用shutil.which，最后尝试常见路径"""
        if browser_name == "default":
            return None
        
        # 检查缓存
        if browser_name in self.browser_path_cache:
            return self.browser_path_cache[browser_name]
        
        exe_name = self.browser_paths.get(browser_name)
        if not exe_name:
            return None
        
        # 1. 首先使用shutil.which快速查找，利用系统PATH
        which_path = shutil.which(exe_name)
        if which_path:
            self.browser_path_cache[browser_name] = which_path
            return which_path
        
        # 2. 注册表查找函数
        def get_reg_value(key_path, value_name, hive=winreg.HKEY_LOCAL_MACHINE):
            """获取注册表值"""
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                    value, _ = winreg.QueryValueEx(key, value_name)
                    return value
            except Exception:
                return None
        
        # 浏览器特定的注册表查找
        browser_reg_paths = {
            "chrome": [
                # Chrome - App Paths
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                # Chrome - Start Menu Internet
                r"SOFTWARE\Clients\StartMenuInternet\Google Chrome\shell\open\command",
                r"SOFTWARE\WOW6432Node\Clients\StartMenuInternet\Google Chrome\shell\open\command"
            ],
            "firefox": [
                # Firefox - App Paths
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe",
                # Firefox - Start Menu Internet
                r"SOFTWARE\Clients\StartMenuInternet\Firefox-308046B0AF4A39CB\shell\open\command",
                r"SOFTWARE\WOW6432Node\Clients\StartMenuInternet\Firefox-308046B0AF4A39CB\shell\open\command"
            ],
            "edge": [
                # Edge - App Paths
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
                # Edge - Start Menu Internet
                r"SOFTWARE\Clients\StartMenuInternet\Microsoft Edge\shell\open\command",
                r"SOFTWARE\WOW6432Node\Clients\StartMenuInternet\Microsoft Edge\shell\open\command"
            ],
            "safari": [
                # Safari - App Paths
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\safari.exe"
            ]
        }
        
        # 3. 优先通过注册表查找
        if browser_name in browser_reg_paths:
            for reg_path in browser_reg_paths[browser_name]:
                try:
                    # 尝试获取注册表值
                    reg_value = get_reg_value(reg_path, "")
                    if reg_value:
                        # 处理带引号的路径
                        if reg_value.startswith('"') and '"' in reg_value[1:]:
                            # 提取引号内的路径
                            browser_path = reg_value.split('"')[1]
                        else:
                            # 提取第一个空格前的路径
                            browser_path = reg_value.split()[0]
                        
                        # 检查路径是否存在
                        if os.path.exists(browser_path):
                            self.browser_path_cache[browser_name] = browser_path
                            return browser_path
                except Exception:
                    continue
        
        # 4. 尝试直接检查常见路径，不进行递归搜索
        common_paths = [
            os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application"),
            r"C:\Program Files\Google\Chrome\Application",
            r"C:\Program Files\Mozilla Firefox",
            r"C:\Program Files (x86)\Google\Chrome\Application",
            r"C:\Program Files (x86)\Mozilla Firefox",
            os.path.expanduser(r"~\AppData\Local\Programs\Microsoft Edge"),
            os.path.expanduser(r"~\AppData\Local\Programs\Firefox"),
            os.path.expanduser(r"~\AppData\Local\Programs\Chrome")
        ]
        
        # 检查常见路径
        for path in common_paths:
            browser_path = os.path.join(path, exe_name)
            if os.path.exists(browser_path):
                self.browser_path_cache[browser_name] = browser_path
                return browser_path
        
        # 5. 移除递归搜索，避免UI阻塞
        # 只有在必要时才返回原始文件名，依赖系统PATH
        result = exe_name
        self.browser_path_cache[browser_name] = result
        return result
    
    def match_rule(self, url, rules):
        """根据URL匹配规则，返回匹配的浏览器名称"""
        try:
            # 解析URL
            actual_url = url
            if actual_url.startswith(f"{self.protocol_name}://"):
                actual_url = actual_url.replace(f"{self.protocol_name}://", "http://")
            
            parsed_url = urlparse(actual_url)
            
            # 查找匹配的规则
            matched_rule = None
            for rule in rules:
                pattern = rule["pattern"]
                if pattern == parsed_url.netloc or f".{pattern}" in parsed_url.netloc or pattern in actual_url:
                    matched_rule = rule
                    break
            
            # 选择浏览器
            if matched_rule:
                return matched_rule["browser"]
            else:
                return "default"
        except Exception as e:
            print(f"匹配规则失败: {e}")
            return "default"
    
    def set_protocol_name(self, protocol_name):
        """设置协议名称"""
        self.protocol_name = protocol_name

# 浏览器路径预扫描线程
class BrowserScannerThread(QThread):
    """预扫描浏览器路径的线程"""
    # 定义信号，用于向主线程发送扫描结果
    scan_finished = pyqtSignal(dict)
    
    def __init__(self, router_engine):
        super().__init__()
        self.router_engine = router_engine
    
    def run(self):
        """线程运行函数，扫描所有支持的浏览器路径"""
        browser_paths_scanned = {}
        
        # 扫描所有支持的浏览器
        for browser_name in self.router_engine.browser_paths.keys():
            if browser_name != "default":
                try:
                    # 调用router_engine的find_browser_path函数扫描路径
                    path = self.router_engine.find_browser_path(browser_name)
                    browser_paths_scanned[browser_name] = path
                except Exception as e:
                    print(f"扫描{browser_name}失败: {e}")
        
        # 发送扫描结果到主线程
        self.scan_finished.emit(browser_paths_scanned)

class TransparentWindow(QMainWindow):
    """透明主窗口，只负责UI渲染和事件捕获"""
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器和路由引擎
        self.config_manager = ConfigManager()
        self.router_engine = RouterEngine()
        
        # 读取配置
        self.config = self.config_manager.read_config()
        
        # 设置窗口属性
        self.setWindowTitle("URL输入框")
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnBottomHint | 
            Qt.Tool
        )
        
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # 初始化窗口大小和位置
        width = self.config.get('window_width', 500)
        height = self.config.get('window_height', 100)
        x = self.config.get('window_x', 100)
        y = self.config.get('window_y', 100)
        
        # 检查窗口大小
        if width < 100 or height < 30:
            width = self.config_manager.DEFAULT_CONFIG['window_width']
            height = self.config_manager.DEFAULT_CONFIG['window_height']
            self.config['window_width'] = width
            self.config['window_height'] = height
            self.config_manager.save_config(self.config)
        
        self.setGeometry(x, y, width, height)
        
        # 设置透明度
        self.setWindowOpacity(self.config.get('opacity', 0.8))
        
        # 初始化缩放比例
        self.scale_factor = self.config.get('scale_factor', 1.0)
        
        # 拖动和缩放相关变量 - 完全分开的状态变量
        # 拖动状态
        self.dragging = False
        self.drag_offset = QPoint()
        # 调整大小状态
        self.resizing = False
        self.resize_start_pos = QPoint()
        self.resize_start_size = QSize()
        # 缩放状态
        self.scaling = False
        self.scale_start_y = 0
        self.base_scale_factor = 1.0
        self.original_aspect_ratio = width / height  # 原始宽高比
        
        # 延迟保存定时器
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_config)
        self.SAVE_DELAY = 500  # 500毫秒延迟保存
        
        # 规则管理
        self.protocol_name = "urlrule"
        self.router_engine.set_protocol_name(self.protocol_name)
        self.script_path = os.path.abspath(__file__)
        self.rules = self.config_manager.read_rules()
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建UI
        self.setup_ui()
        
        # 注册URL协议
        self.register_protocol()
        
        # 设置开机自启动
        if self.config['auto_start']:
            self.set_auto_start(True)
        
        # 托盘图标
        self.tray_icon = None
        self.setup_tray()
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            url = sys.argv[1]
            self.handle_url(url)
        
        # 应用初始缩放设置
        self.resize_widgets()
        
        # 启动浏览器路径预扫描线程
        self.start_browser_scanner()
    
    def start_browser_scanner(self):
        """启动浏览器路径预扫描线程"""
        # 创建扫描线程，传递router_engine
        self.browser_scanner = BrowserScannerThread(self.router_engine)
        
        # 连接信号，接收扫描结果
        self.browser_scanner.scan_finished.connect(self.on_browser_scan_finished)
        
        # 启动线程
        self.browser_scanner.start()
    
    def on_browser_scan_finished(self, scanned_paths):
        """处理浏览器扫描完成信号"""
        print(f"浏览器路径预扫描完成: {scanned_paths}")
    
    def setup_ui(self):
        """设置UI组件"""
        # 设置中央部件透明
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.central_widget.setStyleSheet("background-color: transparent;")
        
        # 主布局
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        
        # 基础尺寸配置
        self.base_entry_width = 250
        self.base_btn_width = 80
        self.base_colon_width = 20
        self.base_component_height = 30
        self.base_font_size = self.config.get('font_size', 12)
        self.border_thickness = self.config.get('border_thickness', 2)
        
        # 字体设置
        self.font_family = self.config.get('font_family', 'Arial')
        # 检查字体是否可用
        font_database = QFontDatabase()
        available_fonts = font_database.families()
        if self.font_family not in available_fonts:
            self.font_family = 'Arial'
            self.config['font_family'] = self.font_family
        
        # 输入框
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入URL...")
        # 设置输入框属性，确保背景透明
        self.url_input.setAttribute(Qt.WA_TranslucentBackground, True)
        self.url_input.setAttribute(Qt.WA_NoSystemBackground, False)
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0.01);
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
        """)
        self.url_input.returnPressed.connect(self.visit_url)
        
        # 添加粘贴按钮
        self.add_paste_button()
        
        # 设置自定义右键菜单
        self.url_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self.url_input.customContextMenuRequested.connect(self.show_context_menu)
        
        # 冒号标签
        self.colon_label = QLabel(":")
        self.colon_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.colon_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-family: {self.font_family};
                font-size: {self.base_font_size * 2}px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.01);
            }}
        """)
        
        # 访问按钮
        self.visit_btn = QPushButton("访问")
        self.visit_btn.setAttribute(Qt.WA_TranslucentBackground, True)
        self.visit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.01);
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
        """)
        self.visit_btn.clicked.connect(self.visit_url)
        
        # 布局组件
        main_layout.addWidget(self.url_input, 1)
        main_layout.addWidget(self.colon_label)
        main_layout.addWidget(self.visit_btn)
    
    def add_paste_button(self):
        """添加粘贴按钮到输入框右侧"""
        # 创建粘贴图标
        paste_icon = self.create_paste_icon()
        
        # 创建动作
        paste_action = QAction(paste_icon, "粘贴", self)
        paste_action.triggered.connect(self.paste_from_clipboard)
        
        # 添加到输入框右侧
        self.url_input.addAction(paste_action, QLineEdit.TrailingPosition)
    
    def create_paste_icon(self):
        """动态绘制粘贴图标"""
        size = 16
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔和画刷
        pen = QPen(Qt.white, 1.5)
        painter.setPen(pen)
        
        # 绘制剪贴板形状
        # 主体矩形
        painter.drawRect(2, 4, size-4, size-6)
        # 顶部矩形
        painter.drawRect(3, 2, size-6, 3)
        # 中间线条
        painter.drawLine(4, 8, size-4, 8)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴内容"""
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            # 去除首尾空格（如果看起来像URL）
            if any(char in clipboard_text for char in ['.', ':', '/', '\\']):
                clipboard_text = clipboard_text.strip()
            
            self.url_input.setText(clipboard_text)
    
    def show_context_menu(self, position):
        """显示自定义右键菜单"""
        # 创建上下文菜单
        menu = QMenu(self.url_input)
        
        # 设置菜单样式
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;   /* 纯白背景 */
                color: #333333;              /* 深灰文字，确保可读 */
                border: 1px solid #cccccc;   /* 淡灰边框 */
                padding: 5px 0px;            /* 整体内边距 */
            }
            QMenu::item {
                padding: 8px 25px;           /* 增加选项间距，更现代 */
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #f2f2f2;   /* 悬停时的“第二种白” */
                color: #000000;              /* 悬停时文字变纯黑 */
            }
            QMenu::separator {
                height: 1px;
                background: #eeeeee;         /* 分割线也用淡白色 */
                margin: 4px 10px;
            }
        """)
        
        # 添加菜单选项
        undo_action = menu.addAction("撤销")
        undo_action.triggered.connect(self.url_input.undo)
        
        redo_action = menu.addAction("恢复")
        redo_action.triggered.connect(self.url_input.redo)
        
        menu.addSeparator()
        
        cut_action = menu.addAction("剪切")
        cut_action.triggered.connect(self.url_input.cut)
        
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self.url_input.copy)
        
        paste_action = menu.addAction("粘贴")
        paste_action.triggered.connect(self.paste_from_clipboard)
        
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.url_input.del_())
        
        menu.addSeparator()
        
        select_all_action = menu.addAction("全选")
        select_all_action.triggered.connect(self.url_input.selectAll)
        
        # 显示菜单
        menu.exec_(self.url_input.mapToGlobal(position))
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制透明背景
        painter.fillRect(self.rect(), QColor(255, 0, 255, 0))
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 重置所有状态
        self.dragging = False
        self.resizing = False
        self.scaling = False
        
        if event.button() == Qt.LeftButton:
            # 左键点击处理
            # 检查是否点击在冒号标签上
            if self.colon_label.geometry().contains(event.pos()):
                # 左键按住冒号：移动窗口
                self.dragging = True
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            elif not (self.url_input.geometry().contains(event.pos()) or \
                    self.visit_btn.geometry().contains(event.pos())):
                # 检查是否点击在边框区域
                border_size = 10
                rect = self.rect()
                if event.pos().x() < border_size or \
                   event.pos().x() > rect.width() - border_size or \
                   event.pos().y() < border_size or \
                   event.pos().y() > rect.height() - border_size:
                    # 左键点击边框：调整窗口大小
                    self.resizing = True
                    self.resize_start_pos = event.globalPos()
                    self.resize_start_size = self.size()
                    event.accept()
        elif event.button() == Qt.RightButton:
            # 右键点击处理
            # 检查是否点击在冒号标签上
            if self.colon_label.geometry().contains(event.pos()):
                # 右键按住冒号：调整窗口缩放比例
                self.scaling = True
                self.scale_start_y = event.globalPos().y()
                self.base_scale_factor = self.scale_factor
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and not self.config['lock_position']:
            # 左键拖动冒号：移动窗口
            new_pos = event.globalPos() - self.drag_offset
            self.move(new_pos)
            event.accept()
            # 延迟保存
            self.delay_save_config()
        elif self.resizing and not self.config['lock_size']:
            # 左键拖动边框：调整窗口大小
            delta = event.globalPos() - self.resize_start_pos
            new_width = max(200, self.resize_start_size.width() + delta.x())
            new_height = max(60, self.resize_start_size.height() + delta.y())
            self.resize(new_width, new_height)
            event.accept()
            # 延迟保存
            self.delay_save_config()
        elif self.scaling and not self.config['lock_size']:
            # 右键拖动冒号：调整窗口缩放比例
            # 计算鼠标Y坐标的变化量
            delta_y = self.scale_start_y - event.globalPos().y()
            
            # 根据Y坐标变化量调整缩放比例
            scale_step = 0.005  # 缩放步长
            scale_change = delta_y * scale_step
            new_scale = max(0.5, min(3.0, self.base_scale_factor + scale_change))
            
            # 只有当缩放比例有明显变化时才更新
            if abs(new_scale - self.scale_factor) > 0.01:
                self.scale_factor = new_scale
                
                if self.config.get('lock_ratio', True):
                    # 锁定比例：同时调整宽度和高度，保持原始宽高比
                    scaled_height = int(round(self.base_component_height * self.scale_factor))
                    scaled_width = int(round(scaled_height * self.original_aspect_ratio))
                    # 调整窗口大小
                    self.resize(scaled_width, scaled_height)
                    # 更新组件大小
                    self.resize_widgets()
                else:
                    # 不锁定比例：只调整字体大小和窗口高度，宽度保持不变
                    self.resize_widgets()
                
                event.accept()
                # 延迟保存
                self.delay_save_config()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        # 重置所有状态
        self.dragging = False
        self.resizing = False
        self.scaling = False
        # 立即保存
        self.save_config()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件"""
        if self.config['lock_size']:
            return
        
        scale_step = 0.1
        if event.angleDelta().y() > 0:
            new_scale = self.scale_factor + scale_step
        else:
            new_scale = max(0.5, self.scale_factor - scale_step)
        
        self.scale_factor = new_scale
        self.resize_widgets()
        self.delay_save_config()
    
    def resize_widgets(self):
        """调整所有组件大小"""
        scaled_font_size = int(round(self.base_font_size * self.scale_factor))
        component_height = int(round(self.base_component_height * self.scale_factor))
        
        # 更新输入框样式
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0.01);
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
        """)
        
        # 更新冒号标签样式
        self.colon_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-family: {self.font_family};
                font-size: {scaled_font_size * 2}px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.01);
            }}
        """)
        
        # 更新按钮样式
        self.visit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.01);
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
        """)
        
        # 调整组件大小
        self.url_input.setMinimumHeight(component_height)
        self.visit_btn.setMinimumHeight(component_height)
        self.colon_label.setMinimumHeight(component_height)
        
        # 更新配置
        self.config['window_width'] = self.width()
        self.config['window_height'] = self.height()
        self.config['window_x'] = self.x()
        self.config['window_y'] = self.y()
        self.config['scale_factor'] = self.scale_factor
    
    def delay_save_config(self):
        """延迟保存配置"""
        self.save_timer.start(self.SAVE_DELAY)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            self.config_manager.save_config(self.config)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def save_rules(self, rules):
        """保存规则到文件"""
        return self.config_manager.save_rules(rules)
    
    def visit_url(self):
        """访问输入的URL"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入URL")
            return
        
        # URL格式验证
        if not (url.startswith(('http://', 'https://', f'{self.protocol_name}://')) or \
                '.' in url or ':' in url):
            QMessageBox.warning(self, "警告", "请输入有效的URL格式")
            return
        
        # 补全协议
        if not url.startswith(('http://', 'https://', f'{self.protocol_name}://')):
            url = f'{self.protocol_name}://{url}'
        
        self.handle_url(url)
        # 清空输入框
        self.url_input.clear()
    
    def handle_url(self, url):
        """处理URL请求"""
        try:
            # 解析URL
            actual_url = url
            if actual_url.startswith(f"{self.protocol_name}://"):
                actual_url = actual_url.replace(f"{self.protocol_name}://", "http://")
            
            # 使用RouterEngine匹配规则
            browser = self.router_engine.match_rule(url, self.rules)
            
            # 调用浏览器 - 使用RouterEngine的find_browser_path
            browser_exe = None
            if browser != "default":
                browser_exe = self.router_engine.find_browser_path(browser)
            
            if browser_exe:
                # 安全执行：去掉shell=True，直接使用列表参数
                subprocess.Popen([browser_exe, actual_url])
            else:
                # 使用Python内置的os.startfile方法，安全打开默认浏览器
                try:
                    os.startfile(actual_url)
                except Exception as e1:
                    print(f"使用os.startfile打开URL失败: {e1}")
                    try:
                        # 回退方案1：使用webbrowser模块，这是最安全的兜底
                        webbrowser.open(actual_url)
                    except Exception as e2:
                        print(f"使用webbrowser打开URL失败: {e2}")
                        # 最后的兜底方案：使用subprocess，不使用shell=True
                        try:
                            # 尝试使用系统默认浏览器的通用方法
                            subprocess.Popen(['cmd', '/c', 'start', '', actual_url], shell=False)
                        except Exception as e3:
                            print(f"所有打开URL的方法都失败了: {e3}")
                            QMessageBox.critical(self, "错误", f"无法打开浏览器: {str(e3)}")
            
            return True
        except Exception as e:
            print(f"处理URL失败: {e}")
            QMessageBox.critical(self, "错误", f"处理URL失败: {str(e)}")
            return False
    
    def register_protocol(self):
        """注册URL协议"""
        try:
            # 尝试使用HKEY_CURRENT_USER注册，不需要管理员权限
            # 创建协议键
            key_path = rf"Software\Classes\{self.protocol_name}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{self.protocol_name} Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # 设置默认图标
            icon_path = rf"{key_path}\DefaultIcon"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{sys.executable},0")
            
            # 设置命令处理
            command_path = rf"{key_path}\shell\open\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path) as key:
                pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                if not os.path.exists(pythonw_path):
                    pythonw_path = sys.executable
                
                command = f'"{pythonw_path}" "{self.script_path}" "%1"'
                winreg.SetValue(key, "", winreg.REG_SZ, command)
            
            return True
        except Exception as e:
            print(f"注册协议失败: {e}")
            # 提示用户以管理员身份运行
            QMessageBox.warning(
                self, 
                "注册失败", 
                f"URL协议注册失败: {str(e)}\n\n请尝试以管理员身份运行程序，或手动注册协议。"
            )
            return False
    
    def setup_tray(self):
        """设置Qt原生托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon()
        
        # 设置图标
        if os.path.exists(ICON_FILE):
            self.tray_icon.setIcon(QIcon(ICON_FILE))
        else:
            # 创建默认图标 - 使用PyQt5原生功能，不依赖Pillow
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(255, 0, 255))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(Qt.white, 2))
            painter.setFont(QFont("Arial", 28, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "URL")
            painter.end()
            
            self.tray_icon.setIcon(QIcon(pixmap))
        
        # 设置托盘提示
        self.tray_icon.setToolTip("URL浏览器规则")
        
        # 创建托盘菜单
        self.create_tray_menu()
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def create_tray_menu(self):
        """创建托盘菜单"""
        # 清空现有菜单
        self.tray_menu = QMenu()
        
        # 设置菜单项
        self.tray_menu.addAction("设置", self.show_settings)
        
        # 开机自启动
        auto_start_action = QAction(f"{'✓ ' if self.config['auto_start'] else ''}开机自启动", self.tray_menu)
        auto_start_action.triggered.connect(self.toggle_auto_start)
        self.tray_menu.addAction(auto_start_action)
        
        # 锁定位置
        lock_pos_action = QAction(f"{'✓ ' if self.config['lock_position'] else ''}锁定位置", self.tray_menu)
        lock_pos_action.triggered.connect(self.toggle_lock_position)
        self.tray_menu.addAction(lock_pos_action)
        
        # 锁定大小
        lock_size_action = QAction(f"{'✓ ' if self.config['lock_size'] else ''}锁定大小", self.tray_menu)
        lock_size_action.triggered.connect(self.toggle_lock_size)
        self.tray_menu.addAction(lock_size_action)
        
        # 锁定比例
        lock_ratio_action = QAction(f"{'✓ ' if self.config.get('lock_ratio', True) else ''}锁定比例", self.tray_menu)
        lock_ratio_action.triggered.connect(self.toggle_lock_ratio)
        self.tray_menu.addAction(lock_ratio_action)
        
        # 退出选项
        self.tray_menu.addAction("退出", self.exit_program)
        
        # 设置菜单
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件处理"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_settings()
    
    def toggle_auto_start(self):
        """切换开机自启动"""
        self.config['auto_start'] = not self.config['auto_start']
        self.set_auto_start(self.config['auto_start'])
        self.save_config()
        self.create_tray_menu()
    
    def toggle_lock_position(self):
        """切换锁定位置"""
        self.config['lock_position'] = not self.config['lock_position']
        self.save_config()
        self.create_tray_menu()
    
    def toggle_lock_size(self):
        """切换锁定大小"""
        self.config['lock_size'] = not self.config['lock_size']
        self.save_config()
        self.create_tray_menu()
    
    def update_tray_menu(self):
        """更新托盘菜单 - 使用create_tray_menu替代"""
        self.create_tray_menu()
    
    def toggle_lock_ratio(self):
        """切换锁定比例"""
        self.config['lock_ratio'] = not self.config.get('lock_ratio', True)
        self.save_config()
        self.create_tray_menu()
    
    def show_settings(self):
        """显示设置窗口"""
        # 创建设置窗口
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("URL浏览器规则设置")
        settings_dialog.setGeometry(200, 200, 800, 600)
        
        # 标签页
        tab_widget = QTabWidget(settings_dialog)
        
        # 规则管理标签页
        rules_tab = QWidget()
        self.setup_rules_tab(rules_tab)
        tab_widget.addTab(rules_tab, "规则管理")
        
        # 外观设置标签页
        appearance_tab = QWidget()
        self.setup_appearance_tab(appearance_tab)
        tab_widget.addTab(appearance_tab, "外观设置")
        
        # 布局
        layout = QVBoxLayout(settings_dialog)
        layout.addWidget(tab_widget)
        
        settings_dialog.exec_()
    
    def setup_rules_tab(self, parent):
        """设置规则管理标签页"""
        layout = QHBoxLayout(parent)
        
        # 规则列表
        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["ID", "匹配模式", "浏览器", "描述"])
        self.rules_tree.setColumnWidth(0, 50)
        self.rules_tree.setColumnWidth(1, 150)
        self.rules_tree.setColumnWidth(2, 100)
        self.rules_tree.setColumnWidth(3, 300)
        
        # 加载规则
        self.load_rules_to_tree()
        
        # 按钮布局
        button_layout = QVBoxLayout()
        
        add_btn = QPushButton("添加规则")
        add_btn.clicked.connect(self.add_rule)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑规则")
        edit_btn.clicked.connect(self.edit_rule)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除规则")
        delete_btn.clicked.connect(self.delete_rule)
        button_layout.addWidget(delete_btn)
        
        # 批量导入按钮
        import_btn = QPushButton("批量导入")
        import_btn.clicked.connect(self.import_rules)
        button_layout.addWidget(import_btn)
        
        button_layout.addStretch()
        
        # 组合布局
        layout.addWidget(self.rules_tree)
        layout.addLayout(button_layout)
    
    def setup_appearance_tab(self, parent):
        """设置外观设置标签页"""
        layout = QGridLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 字体类型
        layout.addWidget(QLabel("字体类型:"), 0, 0)
        self.font_combo = QComboBox()
        font_database = QFontDatabase()
        self.font_combo.addItems(font_database.families())
        self.font_combo.setCurrentText(self.font_family)
        layout.addWidget(self.font_combo, 0, 1)
        
        # 字体大小
        layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.base_font_size)
        layout.addWidget(self.font_size_spin, 1, 1)
        
        # 透明度
        layout.addWidget(QLabel("窗口透明度:"), 2, 0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.config.get('opacity', 0.8) * 100))
        layout.addWidget(self.opacity_slider, 2, 1)
        
        self.opacity_label = QLabel(f"{self.config.get('opacity', 0.8):.1f}")
        layout.addWidget(self.opacity_label, 2, 2)
        
        # 边框厚度
        layout.addWidget(QLabel("边框厚度:"), 3, 0)
        self.border_spin = QSpinBox()
        self.border_spin.setRange(1, 5)
        self.border_spin.setValue(self.border_thickness)
        layout.addWidget(self.border_spin, 3, 1)
        
        # 保存按钮
        save_btn = QPushButton("保存外观设置")
        save_btn.clicked.connect(self.save_appearance_settings)
        layout.addWidget(save_btn, 4, 0, 1, 3)
        
        # 恢复默认缩放按钮
        restore_btn = QPushButton("恢复默认缩放")
        restore_btn.clicked.connect(self.restore_default_scaling)
        layout.addWidget(restore_btn, 5, 0, 1, 3)
    
    def load_rules_to_tree(self):
        """加载规则到树形视图"""
        self.rules_tree.clear()
        # 重新读取规则，确保数据最新
        self.rules = self.config_manager.read_rules()
        for rule in self.rules:
            item = QTreeWidgetItem([
                str(rule["id"]),
                rule["pattern"],
                rule["browser"],
                rule["description"]
            ])
            self.rules_tree.addTopLevelItem(item)
    
    def add_rule(self):
        """添加新规则"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加规则")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QFormLayout(dialog)
        
        # 匹配模式
        pattern_edit = QLineEdit()
        layout.addRow("匹配模式:", pattern_edit)
        
        # 浏览器
        browser_combo = QComboBox()
        browser_combo.addItems(RouterEngine.BROWSER_PATHS.keys())
        layout.addRow("浏览器:", browser_combo)
        
        # 描述
        description_edit = QLineEdit()
        layout.addRow("描述:", description_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_():
            pattern = pattern_edit.text().strip()
            if not pattern:
                QMessageBox.warning(self, "警告", "匹配模式不能为空")
                return
            
            # 验证规则
            if len(pattern) < 2:
                QMessageBox.warning(self, "警告", "匹配模式长度不能少于2个字符")
                return
            
            # 检查重复
            for rule in self.rules:
                if rule["pattern"] == pattern and rule["browser"] == browser_combo.currentText():
                    QMessageBox.warning(self, "警告", "已存在相同的规则")
                    return
            
            # 创建新规则，使用ConfigManager获取下一个ID
            new_id = self.config_manager.get_next_rule_id(self.rules)
            new_rule = {
                "id": new_id,
                "pattern": pattern,
                "browser": browser_combo.currentText(),
                "description": description_edit.text().strip()
            }
            
            self.rules.append(new_rule)
            self.save_rules(self.rules)
            self.load_rules_to_tree()
    
    def edit_rule(self):
        """编辑选中的规则"""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要编辑的规则")
            return
        
        item = selected_items[0]
        rule_id = int(item.text(0))
        rule = next((r for r in self.rules if r["id"] == rule_id), None)
        
        if not rule:
            QMessageBox.critical(self, "错误", "未找到选中的规则")
            return
        
        from PyQt5.QtWidgets import QDialog, QFormLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑规则")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QFormLayout(dialog)
        
        # 匹配模式
        pattern_edit = QLineEdit(rule["pattern"])
        layout.addRow("匹配模式:", pattern_edit)
        
        # 浏览器
        browser_combo = QComboBox()
        browser_combo.addItems(RouterEngine.BROWSER_PATHS.keys())
        browser_combo.setCurrentText(rule["browser"])
        layout.addRow("浏览器:", browser_combo)
        
        # 描述
        description_edit = QLineEdit(rule["description"])
        layout.addRow("描述:", description_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_():
            pattern = pattern_edit.text().strip()
            if not pattern:
                QMessageBox.warning(self, "警告", "匹配模式不能为空")
                return
            
            # 验证规则
            if len(pattern) < 2:
                QMessageBox.warning(self, "警告", "匹配模式长度不能少于2个字符")
                return
            
            # 检查重复（排除当前规则）
            for r in self.rules:
                if r["id"] != rule_id and r["pattern"] == pattern and r["browser"] == browser_combo.currentText():
                    QMessageBox.warning(self, "警告", "已存在相同的规则")
                    return
            
            # 更新规则
            rule["pattern"] = pattern
            rule["browser"] = browser_combo.currentText()
            rule["description"] = description_edit.text().strip()
            
            self.save_rules(self.rules)
            self.load_rules_to_tree()
    
    def delete_rule(self):
        """删除选中的规则"""
        selected_items = self.rules_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的规则")
            return
        
        item = selected_items[0]
        rule_id = int(item.text(0))
        rule = next((r for r in self.rules if r["id"] == rule_id), None)
        
        if not rule:
            QMessageBox.critical(self, "错误", "未找到选中的规则")
            return
        
        if QMessageBox.question(self, "确认", f"确定要删除规则 '{rule['description']}' 吗？") == QMessageBox.Yes:
            self.rules = [r for r in self.rules if r["id"] != rule_id]
            self.save_rules(self.rules)
            self.load_rules_to_tree()
    
    def import_rules(self):
        """批量导入规则"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QComboBox, QDialogButtonBox, QFileDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("批量导入规则")
        dialog.setGeometry(300, 300, 600, 450)
        
        layout = QVBoxLayout(dialog)
        
        # 说明
        info_label = QLabel("请输入URL列表，每行一个，然后选择浏览器：")
        layout.addWidget(info_label)
        
        # 文本编辑区
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("输入URL列表，每行一个...")
        layout.addWidget(text_edit)
        
        # 浏览器选择区
        browser_layout = QHBoxLayout()
        browser_label = QLabel("选择浏览器：")
        browser_layout.addWidget(browser_label)
        
        browser_combo = QComboBox()
        browser_combo.addItems(RouterEngine.BROWSER_PATHS.keys())
        browser_combo.setCurrentText("chrome")  # 默认选择chrome
        browser_layout.addWidget(browser_combo)
        
        browser_layout.addStretch()
        layout.addLayout(browser_layout)
        
        # 导入文件按钮
        file_btn = QPushButton("从文件导入")
        
        def import_from_file():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择规则文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        text_edit.setPlainText(content)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"读取文件失败: {e}")
        
        file_btn.clicked.connect(import_from_file)
        layout.addWidget(file_btn)
        
        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        if dialog.exec_():
            text = text_edit.toPlainText().strip()
            if not text:
                return
            
            # 获取选择的浏览器
            selected_browser = browser_combo.currentText()
            
            # 解析规则
            lines = text.split('\n')
            imported_count = 0
            error_count = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                pattern = line.strip()
                # 描述使用默认格式
                description = f"使用{selected_browser}"
                
                # 检查重复
                duplicate = False
                for rule in self.rules:
                    if rule["pattern"] == pattern and rule["browser"] == selected_browser:
                        duplicate = True
                        break
                
                if not duplicate:
                    # 获取下一个ID，使用ConfigManager的方法
                    new_id = self.config_manager.get_next_rule_id(self.rules)
                    
                    # 添加新规则到内存
                    new_rule = {
                        "id": new_id,
                        "pattern": pattern,
                        "browser": selected_browser,
                        "description": description
                    }
                    self.rules.append(new_rule)
                    imported_count += 1
            
            # 保存到文件
            self.save_rules(self.rules)
            
            # 刷新规则列表
            self.load_rules_to_tree()
            
            # 显示结果
            QMessageBox.information(self, "成功", f"批量导入完成：成功 {imported_count} 条，失败 {error_count} 条")
    
    def save_appearance_settings(self):
        """保存外观设置"""
        # 更新配置
        self.font_family = self.font_combo.currentText()
        self.config['font_family'] = self.font_family
        
        self.base_font_size = self.font_size_spin.value()
        self.config['font_size'] = self.base_font_size
        
        opacity = self.opacity_slider.value() / 100.0
        self.config['opacity'] = opacity
        self.setWindowOpacity(opacity)
        
        self.border_thickness = self.border_spin.value()
        self.config['border_thickness'] = self.border_thickness
        
        # 保存配置
        self.save_config()
        
        # 更新UI
        self.resize_widgets()
        
        QMessageBox.information(self, "成功", "外观设置已保存")
    
    def restore_default_scaling(self):
        """恢复默认缩放设置"""
        self.scale_factor = 1.0
        self.resize_widgets()
        
        # 居中显示
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # 更新配置
        self.config['window_width'] = self.width()
        self.config['window_height'] = self.height()
        self.config['window_x'] = x
        self.config['window_y'] = y
        self.save_config()
        
        QMessageBox.information(self, "成功", "已恢复默认缩放")
    
    def set_auto_start(self, enable):
        """设置开机自启动"""
        try:
            if enable:
                # 添加到开机自启动
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "URLBrowserRule", 0, winreg.REG_SZ, f'"{sys.executable}" "{self.script_path}"')
            else:
                # 从开机自启动中移除
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, "URLBrowserRule")
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
    
    def exit_program(self):
        """退出程序"""
        # 保存配置
        self.save_config()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

if __name__ == "__main__":
    # 防止多个实例运行
    mutex_name = "URLBrowserRuleAdvancedMutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        print("程序已经在运行中...")
        ctypes.windll.kernel32.CloseHandle(mutex)
        sys.exit(0)
    
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        window = TransparentWindow()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        print(f"程序错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")
    finally:
        # 释放互斥体
        ctypes.windll.kernel32.CloseHandle(mutex)
