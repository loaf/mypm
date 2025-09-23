"""
照片导入进度对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont


class ImportProgressDialog(QDialog):
    """照片导入进度对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.import_worker = None
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("照片导入进度")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 进度信息组
        progress_group = QGroupBox("导入进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 当前文件标签
        self.current_file_label = QLabel("准备开始导入...")
        self.current_file_label.setWordWrap(True)
        progress_layout.addWidget(self.current_file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("成功: 0 | 跳过: 0 | 错误: 0")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        progress_layout.addLayout(stats_layout)
        
        layout.addWidget(progress_group)
        
        # 日志信息组
        log_group = QGroupBox("导入日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.cancel_import)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # 统计变量
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        
    def start_import(self, import_worker):
        """开始导入"""
        self.import_worker = import_worker
        
        # 连接信号
        import_worker.progress_updated.connect(self.update_progress)
        import_worker.photo_imported.connect(self.on_photo_imported)
        import_worker.photo_skipped.connect(self.on_photo_skipped)
        import_worker.error_occurred.connect(self.on_error_occurred)
        import_worker.import_completed.connect(self.on_import_completed)
        
        # 启动工作线程
        import_worker.start()
        
        # 重置界面
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.update_stats()
        self.log_text.clear()
        self.log_text.append("开始导入照片...")
        
    @pyqtSlot(int, int, str)
    def update_progress(self, current, total, current_file):
        """更新进度"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        
        filename = current_file.split('\\')[-1] if '\\' in current_file else current_file.split('/')[-1]
        self.current_file_label.setText(f"正在处理: {filename} ({current}/{total})")
        
    @pyqtSlot(str, str)
    def on_photo_imported(self, source_path, target_path):
        """照片导入成功"""
        self.success_count += 1
        self.update_stats()
        
        filename = source_path.split('\\')[-1] if '\\' in source_path else source_path.split('/')[-1]
        self.log_text.append(f"✓ 成功导入: {filename}")
        
    @pyqtSlot(str, str)
    def on_photo_skipped(self, file_path, reason):
        """照片跳过"""
        self.skip_count += 1
        self.update_stats()
        
        filename = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]
        self.log_text.append(f"⚠ 跳过: {filename} - {reason}")
        
    @pyqtSlot(str, str)
    def on_error_occurred(self, file_path, error_message):
        """发生错误"""
        self.error_count += 1
        self.update_stats()
        
        filename = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]
        self.log_text.append(f"✗ 错误: {filename} - {error_message}")
        
    @pyqtSlot(int, int, int)
    def on_import_completed(self, success, skipped, errors):
        """导入完成"""
        self.current_file_label.setText("导入完成！")
        self.progress_bar.setValue(100)
        
        self.log_text.append(f"\n=== 导入完成 ===")
        self.log_text.append(f"成功: {success} 张")
        self.log_text.append(f"跳过: {skipped} 张")
        self.log_text.append(f"错误: {errors} 张")
        
        # 更新按钮状态
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
    def update_stats(self):
        """更新统计信息"""
        self.stats_label.setText(
            f"成功: {self.success_count} | 跳过: {self.skip_count} | 错误: {self.error_count}"
        )
    
    def add_log(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)
    
    def import_finished(self, success: int, skipped: int, errors: int):
        """导入完成处理"""
        self.on_import_completed(success, skipped, errors)
        
    def cancel_import(self):
        """取消导入"""
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.cancel()
            self.log_text.append("\n用户取消导入...")
            self.current_file_label.setText("正在取消...")
            self.cancel_button.setEnabled(False)
            
    def closeEvent(self, event):
        """关闭事件"""
        if self.import_worker and self.import_worker.isRunning():
            self.import_worker.cancel()
            self.import_worker.wait()  # 等待线程结束
        event.accept()