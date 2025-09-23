#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片管理软件 - 主入口文件
M2阶段：基础UI界面启动
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("照片管理软件")
    app.setApplicationVersion("1.0.0 - M2阶段")
    app.setOrganizationName("MyPhotoApp")
    app.setOrganizationDomain("myphotoapp.local")
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 启用高DPI支持（PyQt6中已默认启用，这些设置可选）
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    try:
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序事件循环
        return app.exec()
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())