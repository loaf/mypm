#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片导入模块 - M3阶段
功能：
1. 支持单文件或目录导入
2. 基于EXIF时间信息或文件修改时间创建yyyy/mm/dd目录结构
3. 计算MD5值，检测重复文件
4. 处理文件名冲突
5. 数据库记录管理
"""

import os
import shutil
import hashlib
import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import logging

# 图像处理和EXIF读取
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    import exifread
except ImportError as e:
    print(f"警告：缺少必要的依赖库 {e}")
    print("请运行：pip install Pillow exifread")

from PyQt6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox, QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QObject

# 导入数据库模块
from db.database import DatabaseManager


class PhotoImportWorker(QThread):
    """照片导入工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度值, 当前文件名
    import_completed = pyqtSignal(dict)      # 导入结果统计
    error_occurred = pyqtSignal(str)         # 错误信息
    
    def __init__(self, files_to_import: List[str], target_library_path: str):
        super().__init__()
        self.files_to_import = files_to_import
        self.target_library_path = target_library_path
        self.db_manager = DatabaseManager()
        self.should_stop = False
        
        # 导入统计
        self.stats = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'error_files': []
        }
    
    def stop_import(self):
        """停止导入"""
        self.should_stop = True
    
    def run(self):
        """执行导入任务"""
        try:
            self.stats['total'] = len(self.files_to_import)
            
            for i, file_path in enumerate(self.files_to_import):
                if self.should_stop:
                    break
                
                # 更新进度
                progress = int((i / self.stats['total']) * 100)
                self.progress_updated.emit(progress, os.path.basename(file_path))
                
                # 导入单个文件
                result = self._import_single_file(file_path)
                
                if result['success']:
                    if result['skipped']:
                        self.stats['skipped'] += 1
                    else:
                        self.stats['imported'] += 1
                else:
                    self.stats['errors'] += 1
                    self.stats['error_files'].append({
                        'file': file_path,
                        'error': result['error']
                    })
            
            # 完成导入
            self.progress_updated.emit(100, "导入完成")
            self.import_completed.emit(self.stats)
            
        except Exception as e:
            self.error_occurred.emit(f"导入过程中发生错误: {str(e)}")
    
    def _import_single_file(self, file_path: str) -> Dict[str, Any]:
        """导入单个文件"""
        try:
            # 检查文件是否为图片
            if not self._is_image_file(file_path):
                return {'success': False, 'error': '不是支持的图片格式'}
            
            # 计算文件MD5和大小
            file_md5 = self._calculate_file_md5(file_path)
            file_size = os.path.getsize(file_path)
            
            # 检查是否已存在
            if self.db_manager.check_duplicate_photo(file_md5, file_size):
                return {'success': True, 'skipped': True}
            
            # 获取照片拍摄时间
            photo_date = self._get_photo_date(file_path)
            
            # 创建目标目录结构
            target_dir = self._create_date_directory(photo_date)
            
            # 复制文件到目标位置
            target_file_path = self._copy_file_with_conflict_resolution(
                file_path, target_dir
            )
            
            # 获取相对路径（相对于照片库根目录）
            relative_path = os.path.relpath(target_file_path, self.target_library_path)
            
            # 保存到数据库
            photo_info = {
                'filename': os.path.basename(target_file_path),
                'file_path': relative_path,
                'file_size': file_size,
                'md5_hash': file_md5,
                'date_taken': photo_date,
                'date_imported': datetime.datetime.now(),
                'original_path': file_path
            }
            
            self.db_manager.add_photo_record(photo_info)
            
            return {'success': True, 'skipped': False}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _is_image_file(self, file_path: str) -> bool:
        """检查文件是否为支持的图片格式"""
        supported_extensions = {
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif',
            '.webp', '.raw', '.cr2', '.nef', '.arw', '.dng'
        }
        return Path(file_path).suffix.lower() in supported_extensions
    
    def _calculate_file_md5(self, file_path: str) -> str:
        """分块计算文件MD5值"""
        hash_md5 = hashlib.md5()
        chunk_size = 8192  # 8KB chunks
        
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def _get_photo_date(self, file_path: str) -> datetime.datetime:
        """获取照片拍摄时间（优先EXIF，其次文件修改时间）"""
        
        # 尝试从EXIF获取时间
        exif_date = self._extract_exif_date(file_path)
        if exif_date:
            return exif_date
        
        # 使用文件修改时间作为备选
        file_mtime = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(file_mtime)
    
    def _extract_exif_date(self, file_path: str) -> Optional[datetime.datetime]:
        """从EXIF信息中提取拍摄时间"""
        
        # 方法1：使用Pillow提取EXIF
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    # 尝试多个可能的时间字段
                    time_tags = [
                        'DateTimeOriginal',    # 原始拍摄时间
                        'DateTime',            # 文件修改时间
                        'DateTimeDigitized'    # 数字化时间
                    ]
                    
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name in time_tags:
                            try:
                                return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            except ValueError:
                                continue
        except Exception:
            pass
        
        # 方法2：使用exifread库
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
                
                # 尝试多个可能的EXIF标签
                exif_time_tags = [
                    'EXIF DateTimeOriginal',
                    'EXIF DateTime',
                    'EXIF DateTimeDigitized',
                    'Image DateTime'
                ]
                
                for tag_name in exif_time_tags:
                    if tag_name in tags:
                        try:
                            time_str = str(tags[tag_name])
                            return datetime.datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            continue
        except Exception:
            pass
        
        return None
    
    def _create_date_directory(self, photo_date: datetime.datetime) -> str:
        """根据日期创建目录结构 yyyy/mm/dd"""
        year = photo_date.strftime('%Y')
        month = photo_date.strftime('%m')
        day = photo_date.strftime('%d')
        
        date_dir = os.path.join(self.target_library_path, 'photos', year, month, day)
        os.makedirs(date_dir, exist_ok=True)
        
        return date_dir
    
    def _copy_file_with_conflict_resolution(self, source_path: str, target_dir: str) -> str:
        """复制文件到目标目录，处理文件名冲突"""
        filename = os.path.basename(source_path)
        name, ext = os.path.splitext(filename)
        
        target_path = os.path.join(target_dir, filename)
        counter = 1
        
        # 处理文件名冲突
        while os.path.exists(target_path):
            new_filename = f"{name}_{counter:03d}{ext}"
            target_path = os.path.join(target_dir, new_filename)
            counter += 1
        
        # 复制文件
        shutil.copy2(source_path, target_path)
        return target_path


class PhotoImporter:
    """照片导入管理器"""
    
    def __init__(self, library_path: str):
        self.library_path = library_path
        self.db_manager = DatabaseManager()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def select_files_dialog(self, parent=None) -> List[str]:
        """显示文件选择对话框"""
        file_dialog = QFileDialog(parent)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp *.raw *.cr2 *.nef *.arw *.dng);;所有文件 (*)"
        )
        
        if file_dialog.exec():
            return file_dialog.selectedFiles()
        return []
    
    def select_directory_dialog(self, parent=None) -> str:
        """显示目录选择对话框"""
        directory = QFileDialog.getExistingDirectory(
            parent,
            "选择包含照片的目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        return directory
    
    def scan_directory_for_images(self, directory: str) -> List[str]:
        """扫描目录中的所有图片文件"""
        image_files = []
        supported_extensions = {
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif',
            '.webp', '.raw', '.cr2', '.nef', '.arw', '.dng'
        }
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in supported_extensions:
                    image_files.append(os.path.join(root, file))
        
        return image_files
    
    def import_photos_with_progress(self, files: List[str], parent=None) -> Dict[str, Any]:
        """带进度显示的照片导入"""
        if not files:
            return {'success': False, 'error': '没有选择文件'}
        
        # 创建进度对话框
        progress_dialog = QProgressDialog("正在导入照片...", "取消", 0, 100, parent)
        progress_dialog.setWindowTitle("照片导入")
        progress_dialog.setModal(True)
        progress_dialog.show()
        
        # 创建工作线程
        worker = PhotoImportWorker(files, self.library_path)
        
        # 连接信号
        worker.progress_updated.connect(
            lambda value, filename: self._update_progress(progress_dialog, value, filename)
        )
        
        result = {'success': False}
        
        def on_import_completed(stats):
            nonlocal result
            result = {'success': True, 'stats': stats}
            progress_dialog.close()
        
        def on_error_occurred(error):
            nonlocal result
            result = {'success': False, 'error': error}
            progress_dialog.close()
        
        worker.import_completed.connect(on_import_completed)
        worker.error_occurred.connect(on_error_occurred)
        
        # 处理取消按钮
        progress_dialog.canceled.connect(worker.stop_import)
        
        # 启动导入
        worker.start()
        
        # 等待完成
        while worker.isRunning():
            QApplication.processEvents()
        
        worker.wait()
        
        return result
    
    def _update_progress(self, dialog: QProgressDialog, value: int, filename: str):
        """更新进度对话框"""
        dialog.setValue(value)
        dialog.setLabelText(f"正在处理: {filename}")
        QApplication.processEvents()


def test_photo_importer():
    """测试照片导入功能"""
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("照片导入测试")
            self.setGeometry(100, 100, 400, 200)
            
            # 创建照片导入器
            library_path = os.path.join(os.getcwd(), 'myphotolib')
            self.importer = PhotoImporter(library_path)
            
            # 创建UI
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # 导入文件按钮
            import_files_btn = QPushButton("导入照片文件")
            import_files_btn.clicked.connect(self.import_files)
            layout.addWidget(import_files_btn)
            
            # 导入目录按钮
            import_dir_btn = QPushButton("导入照片目录")
            import_dir_btn.clicked.connect(self.import_directory)
            layout.addWidget(import_dir_btn)
        
        def import_files(self):
            """导入照片文件"""
            files = self.importer.select_files_dialog(self)
            if files:
                result = self.importer.import_photos_with_progress(files, self)
                self._show_result(result)
        
        def import_directory(self):
            """导入照片目录"""
            directory = self.importer.select_directory_dialog(self)
            if directory:
                files = self.importer.scan_directory_for_images(directory)
                if files:
                    result = self.importer.import_photos_with_progress(files, self)
                    self._show_result(result)
                else:
                    QMessageBox.information(self, "提示", "所选目录中没有找到图片文件")
        
        def _show_result(self, result):
            """显示导入结果"""
            if result['success']:
                stats = result['stats']
                message = f"""导入完成！
                
总文件数: {stats['total']}
成功导入: {stats['imported']}
跳过重复: {stats['skipped']}
导入失败: {stats['errors']}"""
                
                if stats['error_files']:
                    message += "\n\n失败文件："
                    for error_file in stats['error_files'][:5]:  # 只显示前5个错误
                        message += f"\n{error_file['file']}: {error_file['error']}"
                
                QMessageBox.information(self, "导入结果", message)
            else:
                QMessageBox.critical(self, "导入失败", result['error'])
    
    # 运行测试
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    # 运行测试
    test_photo_importer()