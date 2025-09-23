"""
照片导入模块 - M3阶段核心功能
支持单文件和目录导入，自动处理EXIF时间、MD5计算、重复检测等
"""

import os
import shutil
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import json

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QFileDialog, QWidget
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

from db.database_manager import DatabaseManager


class PhotoImportWorker(QThread):
    """照片导入工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 当前文件
    photo_imported = pyqtSignal(str, str)  # 源文件路径, 目标路径
    photo_skipped = pyqtSignal(str, str)  # 文件路径, 跳过原因
    error_occurred = pyqtSignal(str, str)  # 文件路径, 错误信息
    import_completed = pyqtSignal(int, int, int)  # 成功数, 跳过数, 错误数
    
    def __init__(self, files: List[str], target_dir: str, db_path: str):
        """
        初始化导入工作线程
        
        Args:
            files: 要导入的文件列表
            target_dir: 目标目录（照片库根目录）
            db_path: 数据库文件路径
        """
        super().__init__()
        self.files = files
        self.target_dir = target_dir
        self.db_path = db_path
        self.is_cancelled = False
        
    def run(self):
        """执行导入任务"""
        success_count = 0
        skip_count = 0
        error_count = 0
        
        with DatabaseManager(self.db_path) as db_manager:
            for i, file_path in enumerate(self.files):
                if self.is_cancelled:
                    break
                    
                self.progress_updated.emit(i + 1, len(self.files), file_path)
                
                try:
                    result = self._import_single_photo(file_path, db_manager)
                    if result == "success":
                        success_count += 1
                    elif result == "skipped":
                        skip_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    self.error_occurred.emit(file_path, str(e))
                    error_count += 1
        
        self.import_completed.emit(success_count, skip_count, error_count)
    
    def cancel(self):
        """取消导入任务"""
        self.is_cancelled = True
    
    def _import_single_photo(self, file_path: str, db_manager: DatabaseManager) -> str:
        """
        导入单张照片
        
        Args:
            file_path: 源文件路径
            db_manager: 数据库管理器
            
        Returns:
            str: "success", "skipped", "error"
        """
        try:
            # 1. 计算文件MD5和大小
            md5_hash, file_size = calculate_file_md5(file_path)
            
            # 2. 检查是否已存在
            if db_manager.photo_exists_by_hash(md5_hash, file_size):
                self.photo_skipped.emit(file_path, "文件已存在（MD5+大小匹配）")
                return "skipped"
            
            # 3. 提取时间信息
            photo_time = extract_photo_datetime(file_path)
            
            # 4. 生成目标路径
            target_path = generate_target_path(
                self.target_dir, 
                file_path, 
                photo_time
            )
            
            # 5. 复制文件（处理重命名冲突）
            final_path = copy_file_with_conflict_resolution(file_path, target_path)
            
            # 6. 获取相对路径
            relative_path = os.path.relpath(final_path, self.target_dir)
            
            # 7. 提取EXIF数据
            exif_data = extract_exif_data(file_path)
            
            # 8. 添加到数据库
            filename = os.path.basename(final_path)
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
            
            photo_id = db_manager.add_photo_record(
                filename=filename,
                relative_path=relative_path,
                md5=md5_hash,
                size=file_size,
                created_at=photo_time.isoformat(),
                photo_type=file_ext,
                exif_data=exif_data
            )
            
            if photo_id:
                self.photo_imported.emit(file_path, final_path)
                return "success"
            else:
                self.error_occurred.emit(file_path, "数据库写入失败")
                return "error"
                
        except Exception as e:
            self.error_occurred.emit(file_path, str(e))
            return "error"


class PhotoImporter:
    """照片导入管理器"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
    
    def __init__(self, target_dir: str, db_path: str):
        """
        初始化照片导入器
        
        Args:
            target_dir: 照片库根目录
            db_path: 数据库文件路径
        """
        self.target_dir = target_dir
        self.db_path = db_path
        
        # 初始化数据库
        self._initialize_database()
        
    def _initialize_database(self):
        """初始化数据库"""
        try:
            db_manager = DatabaseManager(self.db_path)
            if not db_manager.initialize():
                print(f"数据库初始化失败: {self.db_path}")
        except Exception as e:
            print(f"数据库初始化异常: {e}")
        
    def select_files(self, parent: QWidget = None) -> List[str]:
        """
        选择要导入的文件
        
        Args:
            parent: 父窗口
            
        Returns:
            List[str]: 选中的文件路径列表
        """
        file_filter = "图片文件 (*.jpg *.jpeg *.png *.tiff *.tif *.bmp *.gif *.webp);;所有文件 (*.*)"
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "选择要导入的照片",
            "",
            file_filter
        )
        return files
    
    def select_directory(self, parent: QWidget = None) -> Optional[str]:
        """
        选择要导入的目录
        
        Args:
            parent: 父窗口
            
        Returns:
            Optional[str]: 选中的目录路径
        """
        directory = QFileDialog.getExistingDirectory(
            parent,
            "选择要导入的目录"
        )
        return directory if directory else None
    
    def scan_directory(self, directory: str) -> List[str]:
        """
        扫描目录中的所有图片文件
        
        Args:
            directory: 目录路径
            
        Returns:
            List[str]: 图片文件路径列表
        """
        image_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self._is_supported_format(file_path):
                    image_files.append(file_path)
        
        return image_files
    
    def import_single_photo(self, file_path: str) -> Dict[str, Any]:
        """
        导入单张照片
        
        Args:
            file_path: 照片文件路径
            
        Returns:
            dict: 导入结果 {'success': bool, 'target_path': str, 'md5': str, 'error': str}
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {'success': False, 'error': f'文件不存在: {file_path}'}
            
            # 检查是否为支持的图片格式
            if not self._is_supported_format(file_path):
                return {'success': False, 'error': f'不支持的文件格式: {file_path}'}
            
            # 计算MD5和获取文件大小
            md5_hash, file_size = calculate_file_md5(file_path)
            
            # 检查是否已存在
            db_manager = DatabaseManager(self.db_path)
            db_manager.connect()
            db_manager.initialize()
            
            if db_manager.photo_exists_by_hash(md5_hash, file_size):
                db_manager.close()
                return {'success': False, 'error': f'照片已存在 (MD5: {md5_hash})'}
            
            # 获取照片时间
            photo_time = extract_photo_datetime(file_path)
            
            # 生成目标路径
            target_path = generate_target_path(
                self.target_dir, 
                file_path, 
                photo_time
            )
            
            # 复制文件（处理重命名冲突）
            final_path = copy_file_with_conflict_resolution(file_path, target_path)
            
            # 添加到数据库
            filename = os.path.basename(final_path)
            relative_path = os.path.relpath(final_path, self.target_dir)
            
            photo_id = db_manager.add_photo_record(
                filename=filename,
                relative_path=relative_path,
                md5=md5_hash,
                size=file_size,
                created_at=photo_time.isoformat() if photo_time else datetime.now().isoformat()
            )
            
            db_manager.close()
            
            if photo_id:
                return {
                    'success': True, 
                    'target_path': final_path, 
                    'md5': md5_hash,
                    'error': None
                }
            else:
                return {'success': False, 'error': '数据库写入失败'}
                     
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def import_with_progress(self, files: List[str]) -> PhotoImportWorker:
        """
        带进度的导入照片
        
        Args:
            files: 要导入的文件列表
            
        Returns:
            PhotoImportWorker: 导入工作线程
        """
        worker = PhotoImportWorker(files, self.target_dir, self.db_path)
        return worker
    
    def import_photos_with_progress(self, files: List[str], progress_dialog) -> None:
        """
        带进度对话框的导入照片
        
        Args:
            files: 要导入的文件列表
            progress_dialog: 进度对话框实例
        """
        if not files:
            return
        
        # 创建工作线程
        worker = PhotoImportWorker(files, self.target_dir, self.db_path)
        
        # 连接信号到进度对话框
        worker.progress_updated.connect(progress_dialog.update_progress)
        worker.photo_imported.connect(progress_dialog.add_log)
        worker.photo_skipped.connect(lambda path, reason: progress_dialog.add_log(f"跳过: {path} - {reason}"))
        worker.error_occurred.connect(lambda path, error: progress_dialog.add_log(f"错误: {path} - {error}"))
        worker.import_completed.connect(progress_dialog.import_finished)
        
        # 启动工作线程
        worker.start()
        
        # 保存worker引用以防止被垃圾回收
        progress_dialog.worker = worker
    
    def _is_supported_format(self, file_path: str) -> bool:
        """
        检查文件是否为支持的图片格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS


def extract_photo_datetime(file_path: str) -> datetime:
    """
    提取照片的拍摄时间
    优先使用EXIF中的时间信息，如果没有则使用文件修改时间
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        datetime: 照片时间
    """
    try:
        # 尝试从EXIF中提取时间
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
            
            # 优先级顺序：DateTimeOriginal > CreateDate > DateTime
            time_tags = [
                'EXIF DateTimeOriginal',
                'EXIF CreateDate', 
                'EXIF DateTime',
                'Image DateTime'
            ]
            
            for tag_name in time_tags:
                if tag_name in tags:
                    time_str = str(tags[tag_name])
                    try:
                        # EXIF时间格式：YYYY:MM:DD HH:MM:SS
                        return datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        continue
        
        # 如果EXIF中没有时间信息，使用文件修改时间
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime)
        
    except Exception:
        # 出错时使用文件修改时间
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime)


def calculate_file_md5(file_path: str, chunk_size: int = 8192) -> Tuple[str, int]:
    """
    计算文件的MD5值和大小
    使用分块读取处理大文件
    
    Args:
        file_path: 文件路径
        chunk_size: 分块大小（字节）
        
    Returns:
        Tuple[str, int]: (MD5值, 文件大小)
    """
    md5_hash = hashlib.md5()
    file_size = 0
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5_hash.update(chunk)
            file_size += len(chunk)
    
    return md5_hash.hexdigest(), file_size


def generate_target_path(target_dir: str, source_file: str, photo_time: datetime) -> str:
    """
    生成目标文件路径
    按照 yyyy/mm/dd 的目录结构存储
    
    Args:
        target_dir: 目标根目录
        source_file: 源文件路径
        photo_time: 照片时间
        
    Returns:
        str: 目标文件路径
    """
    # 生成日期目录结构
    year = photo_time.strftime('%Y')
    month = photo_time.strftime('%m')
    day = photo_time.strftime('%d')
    
    # 创建目录结构
    date_dir = os.path.join(target_dir, year, month, day)
    os.makedirs(date_dir, exist_ok=True)
    
    # 生成目标文件路径
    filename = os.path.basename(source_file)
    target_path = os.path.join(date_dir, filename)
    
    return target_path


def copy_file_with_conflict_resolution(source_path: str, target_path: str) -> str:
    """
    复制文件并处理文件名冲突
    如果目标文件已存在，自动在文件名后添加序号
    
    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        
    Returns:
        str: 实际的目标文件路径
    """
    if not os.path.exists(target_path):
        shutil.copy2(source_path, target_path)
        return target_path
    
    # 处理文件名冲突
    base_dir = os.path.dirname(target_path)
    filename = os.path.basename(target_path)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_target_path = os.path.join(base_dir, new_filename)
        
        if not os.path.exists(new_target_path):
            shutil.copy2(source_path, new_target_path)
            return new_target_path
        
        counter += 1


def extract_exif_data(file_path: str) -> Optional[Dict[str, Any]]:
    """
    提取照片的EXIF数据
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        Optional[Dict]: EXIF数据字典
    """
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            
            if exif_data is not None:
                # 转换EXIF标签为可读格式
                readable_exif = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    # 只保存字符串和数字类型的值
                    if isinstance(value, (str, int, float)):
                        readable_exif[tag] = value
                    elif isinstance(value, tuple) and len(value) == 2:
                        # 处理分数格式（如光圈值）
                        readable_exif[tag] = f"{value[0]}/{value[1]}"
                
                return readable_exif
                
    except Exception as e:
        print(f"提取EXIF数据失败 {file_path}: {e}")
    
    return None


def test_photo_import():
    """
    测试照片导入功能
    """
    print("=== 照片导入功能测试 ===")
    
    # 测试配置
    test_target_dir = "./test_photo_library"
    test_db_path = "./test_photos.db"
    
    # 创建测试目录
    os.makedirs(test_target_dir, exist_ok=True)
    
    # 初始化导入器
    importer = PhotoImporter(test_target_dir, test_db_path)
    
    # 测试时间提取
    print("\n1. 测试时间提取功能...")
    test_file = "test_image.jpg"  # 需要一个测试图片
    if os.path.exists(test_file):
        photo_time = extract_photo_datetime(test_file)
        print(f"提取的时间: {photo_time}")
    else:
        print("测试图片不存在，跳过时间提取测试")
    
    # 测试MD5计算
    print("\n2. 测试MD5计算功能...")
    if os.path.exists(test_file):
        md5_hash, file_size = calculate_file_md5(test_file)
        print(f"MD5: {md5_hash}")
        print(f"文件大小: {file_size} 字节")
    else:
        print("测试图片不存在，跳过MD5计算测试")
    
    # 测试目标路径生成
    print("\n3. 测试目标路径生成...")
    test_time = datetime(2024, 1, 15, 14, 30, 0)
    target_path = generate_target_path(test_target_dir, "test.jpg", test_time)
    print(f"生成的目标路径: {target_path}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_photo_import()