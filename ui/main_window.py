"""
照片管理软件 - 主窗口界面
M2阶段：基础UI界面实现
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QScrollArea, QLabel,
    QMenuBar, QStatusBar, QFrame, QTextEdit, QApplication, QMessageBox,
    QFileDialog, QListWidget, QListWidgetItem, QPushButton, QButtonGroup,
    QDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QFont, QPixmap, QPalette, QKeySequence, QWheelEvent

from photo_importer import PhotoImporter
from ui.import_progress_dialog import ImportProgressDialog
from core.config_manager import ConfigManager
from db.dao_manager import DAOManager


class MainWindow(QMainWindow):
    """照片管理软件主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化照片导入器
        self.photo_library_path = self.config_manager.get_photo_library_path()
        self.db_path = self.config_manager.get_database_path()  # 数据库路径
        os.makedirs(self.photo_library_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.photo_importer = PhotoImporter(self.photo_library_path, self.db_path)
        
        # 初始化数据库管理器
        self.dao_manager = DAOManager(self.db_path)
        if not self.dao_manager.initialize():
            QMessageBox.critical(self, "错误", "数据库初始化失败！")
            sys.exit(1)
        
        # 存储当前加载的照片数据
        self.current_photos = []
        
        # 单击双击处理
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_single_click)
        self.pending_click_data = None
        
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.load_recent_photos()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle("照片管理软件")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建三栏分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # 创建三个主要区域
        self.setup_left_panel()    # 左侧目录树
        self.setup_center_panel()  # 中间缩略图区域
        self.setup_right_panel()   # 右侧信息面板
        
        # 设置分割器比例 (左:中:右 = 2:5:2)
        self.main_splitter.setSizes([200, 600, 200])
        self.main_splitter.setCollapsible(0, False)  # 左侧面板不可完全折叠
        self.main_splitter.setCollapsible(1, False)  # 中间面板不可完全折叠
        self.main_splitter.setCollapsible(2, False)  # 右侧面板不可完全折叠
        
    def setup_left_panel(self):
        """设置左侧目录树面板"""
        # 创建左侧容器
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加标题
        title_label = QLabel("照片库目录")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc; }")
        left_layout.addWidget(title_label)
        
        # 创建目录树
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabel("文件夹")
        self.directory_tree.setAlternatingRowColors(True)
        self.directory_tree.itemSelectionChanged.connect(self.on_directory_selected)
        left_layout.addWidget(self.directory_tree)
        
        # 添加到分割器
        self.main_splitter.addWidget(left_widget)
        
    def setup_center_panel(self):
        """设置中间照片浏览区域"""
        # 创建中间容器
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加工具栏
        self.setup_thumbnail_toolbar(center_layout)
        
        # 创建缩略图滚动区域
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建缩略图容器
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_container)
        self.thumbnail_layout.setSpacing(5)  # 减少间距从10px到5px
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距从10px到5px
        # 设置网格布局左上对齐
        self.thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # 设置缩略图大小
        self.thumbnail_size = 150  # 默认缩略图大小
        self.min_thumbnail_size = 80
        self.max_thumbnail_size = 300
        
        # 设置滚动区域样式
        self.thumbnail_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        # 安装事件过滤器以处理滚轮事件
        self.thumbnail_scroll.installEventFilter(self)
        
        self.thumbnail_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        center_layout.addWidget(self.thumbnail_scroll)
        
        # 添加到主分割器
        self.main_splitter.addWidget(center_widget)
    
    def setup_thumbnail_toolbar(self, parent_layout):
        """设置缩略图工具栏"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题标签
        title_label = QLabel("照片缩略图")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # 缩放控制
        zoom_label = QLabel("缩放:")
        toolbar_layout.addWidget(zoom_label)
        
        # 缩小按钮
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self.zoom_out_thumbnails)
        toolbar_layout.addWidget(zoom_out_btn)
        
        # 缩放显示
        self.zoom_label = QLabel("150px")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar_layout.addWidget(self.zoom_label)
        
        # 放大按钮
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self.zoom_in_thumbnails)
        toolbar_layout.addWidget(zoom_in_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_thumbnail_zoom)
        toolbar_layout.addWidget(reset_btn)
        
        # 工具栏样式
        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-bottom: 5px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
        
        parent_layout.addWidget(toolbar_widget)
        
    def zoom_in_thumbnails(self):
        """放大缩略图"""
        if self.thumbnail_size < self.max_thumbnail_size:
            self.thumbnail_size += 20
            self.update_thumbnail_size()
    
    def zoom_out_thumbnails(self):
        """缩小缩略图"""
        if self.thumbnail_size > self.min_thumbnail_size:
            self.thumbnail_size -= 20
            self.update_thumbnail_size()
    
    def reset_thumbnail_zoom(self):
        """重置缩略图大小"""
        self.thumbnail_size = 150
        self.update_thumbnail_size()
    
    def update_thumbnail_size(self):
        """更新缩略图大小"""
        self.zoom_label.setText(f"{self.thumbnail_size}px")
        # 重新加载缩略图
        self.load_photo_thumbnails()
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理滚轮缩放"""
        if obj == self.thumbnail_scroll and event.type() == event.Type.Wheel:
            # 检查是否按下Ctrl键
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # 获取滚轮滚动方向
                delta = event.angleDelta().y()
                if delta > 0:
                    self.zoom_in_thumbnails()
                else:
                    self.zoom_out_thumbnails()
                return True  # 事件已处理
        return super().eventFilter(obj, event)
        
    def load_photo_thumbnails(self):
        """加载照片缩略图到网格布局"""
        # 清空现有的缩略图
        for i in reversed(range(self.thumbnail_layout.count())):
            child = self.thumbnail_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 获取当前选中的目录
        current_item = self.directory_tree.currentItem()
        if not current_item:
            return
        
        directory_path = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not directory_path:
            return
        
        # 根据目录类型获取照片数据
        photos = []
        if directory_path == "recent":
            # 最近导入
            photos = self.dao_manager.get_recent_photos(20)
        elif directory_path.startswith("year_"):
            # 按年份筛选
            year = directory_path.split("_")[1]
            photos = self.dao_manager.get_photos_by_year(int(year))
        elif directory_path.startswith("month_"):
            # 按月份筛选
            parts = directory_path.split("_")
            year, month = int(parts[1]), int(parts[2])
            photos = self.dao_manager.get_photos_by_month(year, month)
        else:
            # 普通目录路径，使用目录查询
            photos = self.dao_manager.photo_dao.get_photos_by_directory(directory_path)
        
        if not photos:
            # 显示空状态
            empty_label = QLabel("此目录中没有照片")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    font-size: 16px;
                    padding: 40px;
                    background-color: #f8f9fa;
                    border: 2px dashed #dee2e6;
                    border-radius: 12px;
                }
            """)
            self.thumbnail_layout.addWidget(empty_label, 0, 0, 1, -1)
            return
        
        # 计算每行的列数
        container_width = self.thumbnail_container.width() - 20  # 减去边距（从40减少到20）
        if container_width <= 0:
            container_width = 800  # 默认宽度
        
        cols = max(1, container_width // (self.thumbnail_size + 10))  # 减少间距从20px到10px
        
        # 添加缩略图到网格
        for i, photo in enumerate(photos):
            row = i // cols
            col = i % cols
            
            thumbnail_widget = self.create_thumbnail_widget(photo, i)
            self.thumbnail_layout.addWidget(thumbnail_widget, row, col)
    
    def create_thumbnail_widget(self, photo, index):
        """创建单个缩略图控件"""
        widget = QWidget()
        widget.setFixedSize(self.thumbnail_size, self.thumbnail_size + 40)  # 额外40px用于文件名
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(3, 3, 3, 3)  # 减少内边距从5px到3px
        layout.setSpacing(2)  # 减少间距从5px到2px
        
        # 创建缩略图标签
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(self.thumbnail_size - 10, self.thumbnail_size - 10)
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        # 加载缩略图
        self.load_thumbnail_image(thumbnail_label, photo)
        
        # 创建文件名标签
        filename = os.path.basename(photo.get('path', '未知文件'))
        if len(filename) > 15:
            filename = filename[:12] + "..."
        
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 11px;
                background-color: transparent;
                border: none;
                padding: 2px;
            }
        """)
        
        layout.addWidget(thumbnail_label)
        layout.addWidget(name_label)
        
        # 设置整体样式
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin: 2px;
            }
            QWidget:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
            }
        """)
        
        # 绑定点击事件 - 支持单击和双击区分
        widget.mousePressEvent = lambda event: self.on_thumbnail_press(photo, index, event)
        widget.mouseDoubleClickEvent = lambda event: self.on_thumbnail_double_click(photo, index, event)
        
        return widget
    
    def load_thumbnail_image(self, label, photo):
        """加载缩略图图片"""
        # 尝试多种路径方式
        possible_paths = [
            photo.get('path', ''),
            photo.get('file_path', ''),
            os.path.join(self.photo_library_path, photo.get('path', '')),
            os.path.join(self.photo_library_path, photo.get('file_path', ''))
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                try:
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        # 缩放到合适大小
                        scaled_pixmap = pixmap.scaled(
                            self.thumbnail_size - 20, self.thumbnail_size - 20,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        label.setPixmap(scaled_pixmap)
                        return
                except Exception as e:
                    print(f"加载缩略图失败: {e}")
        
        # 如果无法加载图片，显示占位符
        label.setText("无法\n加载")
        label.setStyleSheet(label.styleSheet() + "color: #6c757d; font-size: 12px;")
    
    def on_thumbnail_press(self, photo, index, event):
        """处理缩略图按下事件（用于区分单击和双击）"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 存储点击数据，等待判断是单击还是双击
            self.pending_click_data = (photo, index)
            # 启动定时器，如果在定时器超时前没有双击，则处理为单击
            self.click_timer.start(300)  # 300ms内如果有双击则取消单击
    
    def on_thumbnail_double_click(self, photo, index, event):
        """处理缩略图双击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 停止单击定时器
            self.click_timer.stop()
            self.pending_click_data = None
            
            # 处理双击 - 打开预览窗口
            self.open_photo_preview(photo)
    
    def handle_single_click(self):
        """处理单击事件（定时器超时后调用）"""
        if self.pending_click_data:
            photo, index = self.pending_click_data
            self.pending_click_data = None
            
            # 处理单击 - 显示照片信息
            self.show_photo_info(photo)
    
    def open_photo_preview(self, photo):
        """打开照片预览窗口"""
        # 尝试多种路径方式，与load_thumbnail_image保持一致
        possible_paths = [
            photo.get('path', ''),
            photo.get('file_path', ''),
            os.path.join(self.photo_library_path, photo.get('path', '')),
            os.path.join(self.photo_library_path, photo.get('file_path', ''))
        ]
        
        photo_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                photo_path = path
                break
        
        if photo_path:
            print(f"双击缩略图，打开预览: {photo_path}")
            # 打开预览对话框
            preview_dialog = PhotoPreviewDialog(photo_path, self)
            preview_dialog.exec()
        else:
            print("照片文件不存在或路径无效")
    
    def show_photo_info(self, photo):
        """在右侧面板显示照片信息"""
        print(f"单击缩略图，显示信息: {photo.get('path', 'N/A')}")
        
        # 获取照片路径
        possible_paths = [
            photo.get('path', ''),
            photo.get('file_path', ''),
            os.path.join(self.photo_library_path, photo.get('path', '')),
            os.path.join(self.photo_library_path, photo.get('file_path', ''))
        ]
        
        photo_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                photo_path = path
                break
        
        # 构建信息HTML
        info_html = "<h3>照片信息</h3>"
        
        if photo_path:
            # 基本文件信息
            filename = os.path.basename(photo_path)
            file_size = os.path.getsize(photo_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # 获取图片尺寸
            try:
                pixmap = QPixmap(photo_path)
                if not pixmap.isNull():
                    width = pixmap.width()
                    height = pixmap.height()
                    resolution = f"{width} × {height}"
                else:
                    resolution = "无法获取"
            except:
                resolution = "无法获取"
            
            info_html += f"""
            <p><b>文件名：</b>{filename}</p>
            <p><b>文件大小：</b>{file_size_mb:.2f} MB</p>
            <p><b>分辨率：</b>{resolution}</p>
            <p><b>文件路径：</b>{photo_path}</p>
            """
            
            # 数据库信息
            if photo.get('created_at'):
                info_html += f"<p><b>导入时间：</b>{photo.get('created_at')}</p>"
            if photo.get('file_hash'):
                info_html += f"<p><b>文件哈希：</b>{photo.get('file_hash')[:16]}...</p>"
            
            info_html += "<hr><p><i>双击缩略图可打开预览窗口</i></p>"
        else:
            info_html += """
            <p><b>文件名：</b>文件不存在</p>
            <p><b>状态：</b>文件路径无效或文件已被移动</p>
            <hr>
            <p><i>请检查文件是否存在</i></p>
            """
        
        # 更新右侧信息面板
        self.info_display.setHtml(info_html)
    

        
    def setup_right_panel(self):
        """设置右侧信息面板"""
        # 创建右侧容器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加标题
        title_label = QLabel("照片信息")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc; }")
        right_layout.addWidget(title_label)
        
        # 创建信息显示区域
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("""
            QTextEdit { 
                background-color: #fafafa; 
                border: 1px solid #ddd; 
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        # 设置默认信息
        default_info = """
<h3>照片信息</h3>
<p><b>文件名：</b>暂无选择</p>
<p><b>文件大小：</b>--</p>
<p><b>分辨率：</b>--</p>
<p><b>拍摄时间：</b>--</p>
<p><b>相机型号：</b>--</p>
<p><b>GPS位置：</b>--</p>
<hr>
<p><i>请选择一张照片查看详细信息</i></p>
        """
        self.info_display.setHtml(default_info)
        right_layout.addWidget(self.info_display)
        
        # 添加弹性空间，使信息区域占满剩余空间
        right_layout.addStretch()
        
        # 添加到分割器
        self.main_splitter.addWidget(right_widget)
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        import_file_action = QAction("导入文件(&F)...", self)
        import_file_action.setShortcut("Ctrl+O")
        import_file_action.setStatusTip("导入单个照片文件")
        import_file_action.triggered.connect(self.import_file)
        file_menu.addAction(import_file_action)
        
        import_dir_action = QAction("导入目录(&D)...", self)
        import_dir_action.setShortcut("Ctrl+Shift+O")
        import_dir_action.setStatusTip("导入整个目录的照片")
        import_dir_action.triggered.connect(self.import_directory)
        file_menu.addAction(import_dir_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 配置菜单
        config_menu = menubar.addMenu("配置(&C)")
        
        library_path_action = QAction("设置照片库路径(&L)...", self)
        library_path_action.setStatusTip("设置照片库的存储路径")
        library_path_action.triggered.connect(self.set_library_path)
        config_menu.addAction(library_path_action)
        
        preferences_action = QAction("首选项(&P)...", self)
        preferences_action.setStatusTip("打开应用程序设置")
        preferences_action.triggered.connect(self.open_preferences)
        config_menu.addAction(preferences_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        cleanup_db_action = QAction("整理数据库(&C)...", self)
        cleanup_db_action.setStatusTip("清理数据库中的无效记录")
        cleanup_db_action.triggered.connect(self.cleanup_database)
        tools_menu.addAction(cleanup_db_action)
        
        sync_db_action = QAction("同步数据库(&S)...", self)
        sync_db_action.setStatusTip("同步照片库与数据库")
        sync_db_action.triggered.connect(self.sync_database)
        tools_menu.addAction(sync_db_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)...", self)
        about_action.setStatusTip("关于照片管理软件")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 照片管理软件 M2阶段")
        
    def load_recent_photos(self):
        """从数据库加载最近导入的照片"""
        try:
            # 获取最近导入的照片
            self.current_photos = self.dao_manager.get_recent_photos(20)
            
            # 构建目录树
            self.build_directory_tree()
            
            # 加载缩略图
            self.load_photo_thumbnails()
            
            # 更新状态栏
            photo_count = len(self.current_photos)
            self.status_bar.showMessage(f"已加载 {photo_count} 张最近导入的照片")
            
        except Exception as e:
            print(f"加载最近照片失败: {e}")
            QMessageBox.warning(self, "警告", f"加载照片失败: {str(e)}")
            # 如果数据库为空，显示示例数据
            self.load_sample_data()
    
    def build_directory_tree(self):
        """根据数据库中的照片构建目录树"""
        # 清空现有树
        self.directory_tree.clear()
        
        # 创建根节点
        root_item = QTreeWidgetItem(self.directory_tree)
        root_item.setText(0, "我的照片库")
        root_item.setData(0, Qt.ItemDataRole.UserRole, "root")
        
        # 最近导入节点
        recent_item = QTreeWidgetItem(root_item)
        recent_item.setText(0, f"最近导入 ({len(self.current_photos)})")
        recent_item.setData(0, Qt.ItemDataRole.UserRole, "recent")
        
        if self.current_photos:
            # 按年份分组
            years = {}
            for photo in self.current_photos:
                if photo.get('created_at'):
                    year = photo['created_at'][:4]  # 提取年份
                    if year not in years:
                        years[year] = []
                    years[year].append(photo)
            
            # 创建年份节点
            for year in sorted(years.keys(), reverse=True):
                year_item = QTreeWidgetItem(root_item)
                year_item.setText(0, f"{year}年 ({len(years[year])})")
                year_item.setData(0, Qt.ItemDataRole.UserRole, f"year_{year}")
                
                # 按月份分组
                months = {}
                for photo in years[year]:
                    if photo.get('created_at') and len(photo['created_at']) >= 7:
                        month = photo['created_at'][5:7]  # 提取月份
                        if month not in months:
                            months[month] = []
                        months[month].append(photo)
                
                # 创建月份节点
                for month in sorted(months.keys(), reverse=True):
                    month_item = QTreeWidgetItem(year_item)
                    month_name = f"{int(month)}月 ({len(months[month])})"
                    month_item.setText(0, month_name)
                    month_item.setData(0, Qt.ItemDataRole.UserRole, f"month_{year}_{month}")
        
        # 展开根节点和最近导入节点
        self.directory_tree.expandItem(root_item)
        if recent_item:
            self.directory_tree.setCurrentItem(recent_item)
    
    def load_sample_data(self):
        """加载示例数据到目录树（当数据库为空时使用）"""
        # 创建虚拟的照片库目录结构
        root_item = QTreeWidgetItem(self.directory_tree)
        root_item.setText(0, "我的照片库")
        root_item.setData(0, Qt.ItemDataRole.UserRole, "/myphotolib")
        
        # 提示信息
        empty_item = QTreeWidgetItem(root_item)
        empty_item.setText(0, "暂无照片")
        empty_item.setData(0, Qt.ItemDataRole.UserRole, "empty")
        
        # 展开根节点
        self.directory_tree.expandItem(root_item)
        
        # 显示空的缩略图区域
        self.load_photo_thumbnails()
    
    def on_directory_item_clicked(self, item, column):
        """处理目录树点击事件"""
        directory_path = item.data(0, Qt.ItemDataRole.UserRole)
        if directory_path and directory_path != "empty":
            print(f"选择目录: {directory_path}")
            # 重新加载该目录的缩略图
            self.load_photo_thumbnails()
        

            
    def on_directory_selected(self):
        """目录树选择事件"""
        current_item = self.directory_tree.currentItem()
        if current_item:
            folder_path = current_item.data(0, Qt.ItemDataRole.UserRole)
            folder_name = current_item.text(0)
            self.status_bar.showMessage(f"已选择目录: {folder_name}")
            
            # 加载对应的照片缩略图
            self.load_photo_thumbnails()
            
            print(f"目录选择: {folder_name} -> {folder_path}")
    
    def on_photo_list_item_clicked(self, item):
        """照片列表项点击事件"""
        photo = item.data(Qt.ItemDataRole.UserRole)
        if not photo:
            return
            
        self.status_bar.showMessage(f"已选择照片: {photo['filename']}")
        
        # 格式化文件大小
        size_mb = photo['size'] / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{photo['size'] / 1024:.1f} KB"
        
        # 格式化日期
        created_at = photo.get('created_at', '未知')
        imported_at = photo.get('imported_at', '未知')
        if created_at != '未知':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if imported_at != '未知':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(imported_at.replace('Z', '+00:00'))
                imported_at = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # 获取EXIF信息
        exif_info = ""
        if photo.get('exif_data'):
            exif_data = photo['exif_data']
            if 'Camera' in exif_data:
                exif_info += f"<p><b>相机型号：</b>{exif_data['Camera']}</p>"
            if 'DateTime' in exif_data:
                exif_info += f"<p><b>拍摄时间：</b>{exif_data['DateTime']}</p>"
            if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                exif_info += f"<p><b>分辨率：</b>{exif_data['ImageWidth']} × {exif_data['ImageHeight']}</p>"
            if 'GPS' in exif_data:
                exif_info += f"<p><b>GPS信息：</b>{exif_data['GPS']}</p>"
        
        # 更新右侧信息面板
        photo_info = f"""
<h3>照片信息</h3>
<p><b>文件名：</b>{photo['filename']}</p>
<p><b>文件路径：</b>{photo['path']}</p>
<p><b>文件大小：</b>{size_str}</p>
<p><b>文件类型：</b>{photo['type'].upper()}</p>
<p><b>MD5值：</b>{photo['md5'][:16]}...</p>
<p><b>创建时间：</b>{created_at}</p>
<p><b>导入时间：</b>{imported_at}</p>
{exif_info}
<hr>
<p><i>照片ID: {photo['id']}</i></p>
        """
        self.info_display.setHtml(photo_info)
        
        # 更新预览区域
        self.update_photo_preview(photo)
        
        print(f"照片点击: {photo['filename']} (ID: {photo['id']})")
            
    def on_thumbnail_clicked(self, index):
        """示例缩略图点击事件（兼容性保留）"""
        self.status_bar.showMessage(f"已选择照片 {index+1:02d}")
        
        # 更新右侧信息面板
        sample_info = f"""
<h3>照片信息</h3>
<p><b>文件名：</b>sample_photo_{index+1:02d}.jpg</p>
<p><b>文件大小：</b>2.5 MB</p>
<p><b>分辨率：</b>1920 × 1080</p>
<p><b>拍摄时间：</b>2024-01-{index+1:02d} 14:30:25</p>
<p><b>相机型号：</b>Canon EOS R5</p>
<p><b>GPS位置：</b>北京市朝阳区</p>
<hr>
<p><i>这是示例数据，实际信息将从EXIF中读取</i></p>
        """
        self.info_display.setHtml(sample_info)
        
        # 更新预览区域
        self.preview_label.setText(f"照片 {index+1:02d} 预览\n(占位图片)")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key.Key_Up:
            self.navigate_photo(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_photo(1)
        else:
            super().keyPressEvent(event)
    
    def navigate_photo(self, direction):
        """键盘导航照片 direction: -1向上, 1向下"""
        current_row = self.photo_list.currentRow()
        if current_row == -1:
            # 如果没有选中项，选择第一项
            if self.photo_list.count() > 0:
                self.photo_list.setCurrentRow(0)
            return
        
        new_row = current_row + direction
        if 0 <= new_row < self.photo_list.count():
            self.photo_list.setCurrentRow(new_row)
            # 触发点击事件
            item = self.photo_list.item(new_row)
            if item:
                self.photo_list.itemClicked.emit(item)
        
        print(f"缩略图点击: 照片 {index+1:02d}")
        
    # 菜单槽函数
    def import_file(self):
        """导入文件槽函数"""
        try:
            # 选择文件
            files = self.photo_importer.select_files(self)
            
            if not files:
                return
                
            # 显示确认信息
            reply = QMessageBox.question(
                self,
                "确认导入",
                f"将导入 {len(files)} 个文件到照片库。\n\n"
                f"照片库路径: {self.photo_library_path}\n\n"
                "是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_import(files)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入文件时发生错误：\n{str(e)}")
        
    def import_directory(self):
        """导入目录槽函数"""
        try:
            # 选择目录
            directory = self.photo_importer.select_directory(self)
            
            if not directory:
                return
                
            # 扫描目录中的图片文件
            files = self.photo_importer.scan_directory(directory)
            
            if not files:
                QMessageBox.information(
                    self,
                    "提示",
                    f"在目录 '{directory}' 中未找到支持的图片文件。\n\n"
                    "支持的格式：JPG, JPEG, PNG, BMP, GIF, TIFF"
                )
                return
                
            # 显示确认信息
            reply = QMessageBox.question(
                self,
                "确认导入",
                f"在目录中找到 {len(files)} 个图片文件。\n\n"
                f"源目录: {directory}\n"
                f"照片库路径: {self.photo_library_path}\n\n"
                "是否继续导入？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_import(files)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入目录时发生错误：\n{str(e)}")
        
    def _start_import(self, files):
        """启动导入过程"""
        try:
            # 创建并显示进度对话框
            progress_dialog = ImportProgressDialog(self)
            progress_dialog.show()
            
            # 开始导入
            self.photo_importer.import_photos_with_progress(files, progress_dialog)
            
            # 更新状态栏
            self.status_bar.showMessage(f"开始导入 {len(files)} 个文件...")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动导入时发生错误：\n{str(e)}")

    def set_library_path(self):
        """设置照片库路径槽函数"""
        try:
            # 选择新的照片库目录
            directory = QFileDialog.getExistingDirectory(
                self,
                "选择照片库目录",
                self.photo_library_path,
                QFileDialog.Option.ShowDirsOnly
            )
            
            if directory:
                self.photo_library_path = directory
                self.photo_importer.library_path = directory
                
                # 保存到配置文件
                self.config_manager.set_photo_library_path(directory)
                
                # 确保目录存在
                os.makedirs(directory, exist_ok=True)
                
                self.status_bar.showMessage(f"照片库路径已设置为: {directory}")
                
                QMessageBox.information(
                    self,
                    "设置成功",
                    f"照片库路径已更新为：\n{directory}"
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置照片库路径时发生错误：\n{str(e)}")
        
    def open_preferences(self):
        """打开首选项槽函数"""
        print("首选项 clicked")
        self.status_bar.showMessage("首选项功能 - 待实现")
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "照片管理软件 v1.0\n\n"
                         "一个简单易用的照片管理工具")
    
    def cleanup_database(self):
        """整理数据库：扫描数据库并删除无效记录"""
        try:
            # 显示进度对话框
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("正在整理数据库...", "取消", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.show()
            QApplication.processEvents()
            
            # 获取所有照片记录
            all_photos = self.dao_manager.photo_dao.get_all_photos()
            total_photos = len(all_photos)
            
            if total_photos == 0:
                progress.close()
                QMessageBox.information(self, "整理完成", "数据库中没有照片记录。")
                return
            
            progress.setMaximum(total_photos)
            invalid_count = 0
            
            # 检查每张照片的文件是否存在
            for i, photo in enumerate(all_photos):
                if progress.wasCanceled():
                    break
                
                progress.setValue(i)
                progress.setLabelText(f"正在检查照片 {i+1}/{total_photos}: {photo['filename']}")
                QApplication.processEvents()
                
                # 构建完整路径
                photo_library_path = self.config_manager.get_photo_library_path()
                full_path = os.path.join(photo_library_path, photo['relative_path'])
                
                # 检查文件是否存在
                if not os.path.exists(full_path):
                    # 文件不存在，标记为删除
                    self.dao_manager.photo_dao.delete_photo(photo['id'], soft_delete=True)
                    invalid_count += 1
            
            progress.close()
            
            if not progress.wasCanceled():
                # 刷新界面
                self.load_recent_photos()
                QMessageBox.information(
                    self, 
                    "整理完成", 
                    f"数据库整理完成！\n\n"
                    f"检查了 {total_photos} 张照片\n"
                    f"删除了 {invalid_count} 条无效记录"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"整理数据库时发生错误：\n{str(e)}")
    
    def sync_database(self):
        """同步数据库：扫描照片库并导入新照片"""
        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认同步",
            "同步数据库将扫描整个照片库并导入新照片。\n\n"
            "这个过程可能需要较长时间，特别是当照片库很大时。\n"
            "在同步过程中，请不要关闭程序。\n\n"
            "是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # 首先执行数据库整理
            self._cleanup_database_silent()
            
            # 显示进度对话框
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("正在同步数据库...", "取消", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.show()
            QApplication.processEvents()
            
            # 获取照片库路径
            photo_library_path = self.config_manager.get_photo_library_path()
            if not photo_library_path or not os.path.exists(photo_library_path):
                progress.close()
                QMessageBox.warning(self, "错误", "照片库路径无效或不存在。")
                return
            
            # 扫描照片库
            progress.setLabelText("正在扫描照片库...")
            QApplication.processEvents()
            
            photo_files = []
            supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw'}
            
            for root, dirs, files in os.walk(photo_library_path):
                if progress.wasCanceled():
                    break
                
                for file in files:
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        photo_files.append(os.path.join(root, file))
            
            if progress.wasCanceled():
                progress.close()
                return
            
            total_files = len(photo_files)
            progress.setMaximum(total_files)
            imported_count = 0
            
            # 导入新照片
            for i, file_path in enumerate(photo_files):
                if progress.wasCanceled():
                    break
                
                progress.setValue(i)
                progress.setLabelText(f"正在处理 {i+1}/{total_files}: {os.path.basename(file_path)}")
                QApplication.processEvents()
                
                try:
                    # 检查照片是否已存在
                    import hashlib
                    file_size = os.path.getsize(file_path)
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if not self.dao_manager.photo_dao.photo_exists_by_hash(file_hash, file_size):
                        # 照片不存在，导入
                        result = self.photo_importer.import_single_photo(file_path)
                        if result:
                            imported_count += 1
                except Exception as e:
                    print(f"导入照片失败 {file_path}: {e}")
                    continue
            
            progress.close()
            
            if not progress.wasCanceled():
                # 刷新界面
                self.load_recent_photos()
                QMessageBox.information(
                    self,
                    "同步完成",
                    f"数据库同步完成！\n\n"
                    f"扫描了 {total_files} 个文件\n"
                    f"导入了 {imported_count} 张新照片"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"同步数据库时发生错误：\n{str(e)}")
    
    def _cleanup_database_silent(self):
        """静默整理数据库（不显示进度和结果）"""
        try:
            # 获取所有照片记录
            all_photos = self.dao_manager.photo_dao.get_all_photos()
            
            # 检查每张照片的文件是否存在
            photo_library_path = self.config_manager.get_photo_library_path()
            for photo in all_photos:
                full_path = os.path.join(photo_library_path, photo['relative_path'])
                if not os.path.exists(full_path):
                    # 文件不存在，标记为删除
                    self.dao_manager.photo_dao.delete_photo(photo['id'], soft_delete=True)
                    
        except Exception as e:
            print(f"静默整理数据库时发生错误: {e}")


class PhotoPreviewDialog(QDialog):
    """照片预览对话框"""
    
    def __init__(self, photo_path, parent=None):
        super().__init__(parent)
        self.photo_path = photo_path
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("照片预览")
        self.setModal(True)
        self.resize(800, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
        """)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2b2b2b;")
        
        # 加载图片
        self.load_image()
        
        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)
        
        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 5, 10, 10)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        
        toolbar.addStretch()
        toolbar.addWidget(close_btn)
        layout.addLayout(toolbar)
        
    def load_image(self):
        """加载图片"""
        try:
            if os.path.exists(self.photo_path):
                pixmap = QPixmap(self.photo_path)
                if not pixmap.isNull():
                    # 缩放图片以适应窗口
                    scaled_pixmap = pixmap.scaled(
                        750, 550,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setText("无法加载图片")
                    self.image_label.setStyleSheet("color: white; font-size: 16px;")
            else:
                self.image_label.setText("图片文件不存在")
                self.image_label.setStyleSheet("color: white; font-size: 16px;")
        except Exception as e:
            print(f"加载图片失败: {e}")
            self.image_label.setText("加载图片失败")
            self.image_label.setStyleSheet("color: white; font-size: 16px;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())