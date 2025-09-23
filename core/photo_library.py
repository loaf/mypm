#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片库管理模块
负责照片库的创建、加载、验证和基本管理功能
"""

import os
import shutil
from typing import Optional
from .config_manager import ConfigManager
from db.database import Database


class PhotoLibrary:
    """照片库管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化照片库管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.current_path: Optional[str] = None
        self.database: Optional[Database] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化照片库"""
        # 获取配置中的照片库路径
        library_path = self.config_manager.get_photo_library_path()
        
        # 尝试加载照片库
        if self.load_library(library_path):
            print(f"成功加载照片库: {library_path}")
        else:
            # 如果加载失败，尝试创建新的照片库
            print(f"照片库不存在，正在创建: {library_path}")
            if self.create_library(library_path):
                print(f"成功创建照片库: {library_path}")
            else:
                print(f"创建照片库失败: {library_path}")
    
    def create_library(self, path: str) -> bool:
        """
        创建新的照片库
        
        Args:
            path: 照片库路径
            
        Returns:
            是否创建成功
        """
        try:
            # 创建主目录
            os.makedirs(path, exist_ok=True)
            
            # 创建子目录结构
            subdirs = [
                "photos",      # 存放照片的主目录
                "thumbnails",  # 缩略图缓存
                "temp",        # 临时文件
                "backup"       # 备份文件
            ]
            
            for subdir in subdirs:
                subdir_path = os.path.join(path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
            
            # 初始化数据库
            db_path = os.path.join(path, "library.db")
            self.database = Database(db_path)
            
            if not self.database.initialize():
                print("数据库初始化失败")
                return False
            
            # 创建库信息文件
            self._create_library_info(path)
            
            # 更新当前路径和配置
            self.current_path = path
            self.config_manager.set_photo_library_path(path)
            
            return True
            
        except Exception as e:
            print(f"创建照片库失败: {e}")
            return False
    
    def load_library(self, path: str) -> bool:
        """
        加载现有照片库
        
        Args:
            path: 照片库路径
            
        Returns:
            是否加载成功
        """
        if not self.is_valid_library(path):
            return False
        
        try:
            # 连接数据库
            db_path = os.path.join(path, "library.db")
            self.database = Database(db_path)
            
            if not self.database.connect():
                print(f"连接数据库失败: {db_path}")
                return False
            
            # 更新当前路径和配置
            self.current_path = path
            self.config_manager.set_photo_library_path(path)
            
            return True
            
        except Exception as e:
            print(f"加载照片库失败: {e}")
            return False
    
    def is_valid_library(self, path: str) -> bool:
        """
        检查路径是否为有效的照片库
        
        Args:
            path: 要检查的路径
            
        Returns:
            是否为有效照片库
        """
        if not os.path.exists(path):
            return False
        
        # 检查必要的子目录
        required_dirs = ["photos", "thumbnails"]
        for dir_name in required_dirs:
            if not os.path.exists(os.path.join(path, dir_name)):
                return False
        
        # 检查数据库文件
        db_path = os.path.join(path, "library.db")
        if not os.path.exists(db_path):
            return False
        
        # 检查库信息文件
        info_path = os.path.join(path, ".library_info")
        if not os.path.exists(info_path):
            return False
        
        return True
    
    def _create_library_info(self, path: str) -> None:
        """
        创建库信息文件
        
        Args:
            path: 照片库路径
        """
        import json
        from datetime import datetime
        
        info = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "type": "MyPhotoApp Library",
            "path": path
        }
        
        info_path = os.path.join(path, ".library_info")
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"创建库信息文件失败: {e}")
    
    def get_photos_dir(self) -> str:
        """获取照片存储目录"""
        if not self.current_path:
            raise RuntimeError("照片库未初始化")
        return os.path.join(self.current_path, "photos")
    
    def get_thumbnails_dir(self) -> str:
        """获取缩略图目录"""
        if not self.current_path:
            raise RuntimeError("照片库未初始化")
        return os.path.join(self.current_path, "thumbnails")
    
    def get_temp_dir(self) -> str:
        """获取临时文件目录"""
        if not self.current_path:
            raise RuntimeError("照片库未初始化")
        return os.path.join(self.current_path, "temp")
    
    def get_library_info(self) -> dict:
        """
        获取照片库信息
        
        Returns:
            照片库信息字典
        """
        if not self.current_path:
            return {}
        
        info = {
            "path": self.current_path,
            "is_valid": self.is_valid_library(self.current_path),
            "photos_count": 0,
            "total_size": 0
        }
        
        # 如果数据库可用，获取统计信息
        if self.database:
            try:
                stats = self.database.get_library_stats()
                info.update(stats)
            except Exception as e:
                print(f"获取库统计信息失败: {e}")
        
        return info
    
    def switch_library(self, new_path: str) -> bool:
        """
        切换到另一个照片库
        
        Args:
            new_path: 新照片库路径
            
        Returns:
            是否切换成功
        """
        # 关闭当前数据库连接
        if self.database:
            self.database.close()
            self.database = None
        
        # 加载新照片库
        if self.load_library(new_path):
            print(f"成功切换到照片库: {new_path}")
            return True
        else:
            # 如果切换失败，尝试重新加载原来的库
            if self.current_path:
                self.load_library(self.current_path)
            return False
    
    def close(self) -> None:
        """关闭照片库"""
        if self.database:
            self.database.close()
            self.database = None
        self.current_path = None
    
    def __del__(self):
        """析构函数"""
        self.close()