#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责应用配置的读取、保存和管理
"""

import os
import json
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件名，默认为config.json
        """
        self.config_file = config_file
        self.config_path = os.path.join(os.getcwd(), config_file)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"配置文件已加载: {self.config_path}")
            else:
                # 如果配置文件不存在，创建默认配置
                self._create_default_config()
                print(f"创建默认配置文件: {self.config_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        default_photo_lib = os.path.join(os.getcwd(), "myphotolib")
        
        self._config = {
            "app": {
                "version": "1.0.0",
                "last_opened": None
            },
            "photo_library": {
                "current_path": default_photo_lib,
                "recent_paths": [default_photo_lib]
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "thumbnail_size": 150,
                "show_sidebar": True
            },
            "import": {
                "auto_organize": True,
                "check_duplicates": True,
                "supported_formats": [
                    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif",
                    ".raw", ".cr2", ".nef", ".arw", ".dng",
                    ".mp4", ".avi", ".mov", ".mkv"
                ]
            }
        }
        self.save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键，如 'photo_library.current_path'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_photo_library_path(self) -> str:
        """获取当前照片库路径"""
        return self.get('photo_library.current_path', 
                       os.path.join(os.getcwd(), "myphotolib"))
    
    def set_photo_library_path(self, path: str) -> None:
        """
        设置照片库路径
        
        Args:
            path: 照片库路径
        """
        self.set('photo_library.current_path', path)
        
        # 更新最近使用的路径列表
        recent_paths = self.get('photo_library.recent_paths', [])
        if path in recent_paths:
            recent_paths.remove(path)
        recent_paths.insert(0, path)
        
        # 只保留最近5个路径
        recent_paths = recent_paths[:5]
        self.set('photo_library.recent_paths', recent_paths)
        
        self.save_config()
    
    def get_recent_photo_libraries(self) -> list:
        """获取最近使用的照片库路径列表"""
        return self.get('photo_library.recent_paths', [])
    
    def get_supported_formats(self) -> list:
        """获取支持的文件格式列表"""
        return self.get('import.supported_formats', [])
    
    def get_window_size(self) -> tuple:
        """获取窗口大小"""
        width = self.get('ui.window_width', 1200)
        height = self.get('ui.window_height', 800)
        return (width, height)
    
    def set_window_size(self, width: int, height: int) -> None:
        """设置窗口大小"""
        self.set('ui.window_width', width)
        self.set('ui.window_height', height)
        self.save_config()
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return json.dumps(self._config, indent=2, ensure_ascii=False)