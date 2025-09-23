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
    QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QFont, QPixmap, QPalette

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
        self.db_path = "./db/photos.db"  # 数据库路径
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
        """设置中间缩略图区域"""
        # 创建中间容器
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加标题
        title_label = QLabel("缩略图浏览")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc; }")
        center_layout.addWidget(title_label)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建缩略图容器
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_widget)
        self.thumbnail_layout.setSpacing(10)
        self.thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # TODO: 后续阶段实现多线程缩略图加载
        # 这里需要实现：
        # 1. 异步加载图片缩略图
        # 2. 使用QThread避免UI阻塞
        # 3. 实现缩略图缓存机制
        # 4. 支持大量图片的虚拟化显示
        
        self.scroll_area.setWidget(self.thumbnail_widget)
        center_layout.addWidget(self.scroll_area)
        
        # 添加到分割器
        self.main_splitter.addWidget(center_widget)
        
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
        self.info_display.setMaximumHeight(300)
        self.info_display.setStyleSheet("QTextEdit { background-color: #fafafa; border: 1px solid #ddd; }")
        
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
        
        # 添加预览区域（占位）
        preview_label = QLabel("照片预览")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        right_layout.addWidget(preview_label)
        
        self.preview_area = QLabel()
        self.preview_area.setMinimumHeight(200)
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setStyleSheet("QLabel { background-color: #ffffff; border: 2px dashed #ccc; }")
        self.preview_area.setText("预览区域\n(暂无图片)")
        right_layout.addWidget(self.preview_area)
        
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
        self.load_sample_thumbnails()
    
    def load_photo_thumbnails(self):
        """从数据库照片数据加载缩略图"""
        # 清空现有缩略图
        for i in reversed(range(self.thumbnail_layout.count())):
            child = self.thumbnail_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.current_photos:
            # 如果没有照片，显示提示信息
            no_photos_label = QLabel("暂无照片\n请导入照片到照片库")
            no_photos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_photos_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 40px;
                }
            """)
            self.thumbnail_layout.addWidget(no_photos_label, 0, 0, 1, 4)
            return
        
        # 创建照片缩略图
        for i, photo in enumerate(self.current_photos):
            if i >= 20:  # 最多显示20张
                break
                
            thumbnail = QLabel()
            thumbnail.setFixedSize(120, 120)
            thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail.setStyleSheet("""
                QLabel {
                    background-color: #f5f5f5;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                }
                QLabel:hover {
                    border-color: #007acc;
                    background-color: #f0f8ff;
                }
            """)
            
            # 尝试加载实际缩略图
            thumbnail_path = photo.get('thumbnail_path')
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    pixmap = QPixmap(thumbnail_path)
                    if not pixmap.isNull():
                        # 缩放图片以适应缩略图大小
                        scaled_pixmap = pixmap.scaled(
                            116, 116, 
                            Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        thumbnail.setPixmap(scaled_pixmap)
                    else:
                        thumbnail.setText(f"{photo['filename'][:10]}...\n(缩略图损坏)")
                except Exception as e:
                    print(f"加载缩略图失败: {e}")
                    thumbnail.setText(f"{photo['filename'][:10]}...\n(加载失败)")
            else:
                # 显示文件名作为占位符
                display_name = photo['filename']
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                thumbnail.setText(f"{display_name}\n{photo['type'].upper()}")
            
            # 设置点击事件
            thumbnail.mousePressEvent = lambda event, idx=i: self.on_photo_thumbnail_clicked(idx)
            
            # 添加到网格布局
            row = i // 4
            col = i % 4
            self.thumbnail_layout.addWidget(thumbnail, row, col)
        
    def load_sample_thumbnails(self):
        """加载示例缩略图（占位）"""
        # 清空现有缩略图
        for i in reversed(range(self.thumbnail_layout.count())):
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
            
        # 创建示例缩略图
        for i in range(12):  # 创建12个占位缩略图
            thumbnail = QLabel()
            thumbnail.setFixedSize(120, 120)
            thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                }
                QLabel:hover {
                    border-color: #007acc;
                    background-color: #f0f8ff;
                }
            """)
            thumbnail.setText(f"照片 {i+1:02d}\n(占位)")
            thumbnail.mousePressEvent = lambda event, idx=i: self.on_thumbnail_clicked(idx)
            
            # 添加到网格布局
            row = i // 4
            col = i % 4
            self.thumbnail_layout.addWidget(thumbnail, row, col)
            
    def on_directory_selected(self):
        """目录树选择事件"""
        current_item = self.directory_tree.currentItem()
        if current_item:
            folder_path = current_item.data(0, Qt.ItemDataRole.UserRole)
            folder_name = current_item.text(0)
            self.status_bar.showMessage(f"已选择目录: {folder_name}")
            
            # 根据选择的目录类型加载对应的照片
            if folder_path == "recent":
                # 最近导入
                self.current_photos = self.dao_manager.get_recent_photos(20)
                self.load_photo_thumbnails()
            elif folder_path.startswith("year_"):
                # 按年份筛选
                year = folder_path.split("_")[1]
                self.current_photos = self.dao_manager.get_photos_by_year(int(year))
                self.load_photo_thumbnails()
            elif folder_path.startswith("month_"):
                # 按月份筛选
                parts = folder_path.split("_")
                year, month = int(parts[1]), int(parts[2])
                self.current_photos = self.dao_manager.get_photos_by_month(year, month)
                self.load_photo_thumbnails()
            
            print(f"目录选择: {folder_name} -> {folder_path}")
    
    def on_photo_thumbnail_clicked(self, index):
        """数据库照片缩略图点击事件"""
        if index >= len(self.current_photos):
            return
            
        photo = self.current_photos[index]
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
        full_path = os.path.join(self.photo_library_path, photo['path'])
        if os.path.exists(full_path):
            try:
                pixmap = QPixmap(full_path)
                if not pixmap.isNull():
                    # 缩放图片以适应预览区域
                    scaled_pixmap = pixmap.scaled(
                        self.preview_area.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.preview_area.setPixmap(scaled_pixmap)
                    self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    self.preview_area.setText("图片预览失败")
            except Exception as e:
                print(f"预览图片失败: {e}")
                self.preview_area.setText("图片预览失败")
        else:
            self.preview_area.setText("图片文件不存在")
        
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
        self.preview_area.setText(f"照片 {index+1:02d} 预览\n(占位图片)")
        
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
        """显示关于对话框槽函数"""
        print("关于 clicked")
        self.status_bar.showMessage("关于对话框 - 待实现")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())