#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置数据访问对象 (Config DAO)
封装配置相关的数据库操作，提供清晰的接口
"""

import sqlite3
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from .database import Database


class ConfigDAO:
    """配置数据访问对象"""
    
    def __init__(self, database: Database):
        """
        初始化ConfigDAO
        
        Args:
            database: 数据库实例
        """
        self.db = database
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值，不存在时返回默认值
        """
        try:
            self.db.cursor.execute('''
                SELECT value FROM config WHERE key = ?
            ''', (key,))
            
            result = self.db.cursor.fetchone()
            if result:
                value = result['value']
                # 尝试解析JSON格式的值
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return default
            
        except sqlite3.Error as e:
            print(f"获取配置失败: {e}")
            return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            # 如果值是复杂类型，转换为JSON字符串
            if isinstance(value, (dict, list, tuple)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)
            
            self.db.cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value_str, datetime.now().isoformat()))
            
            self.db.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"设置配置失败: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            配置字典
        """
        configs = {}
        try:
            self.db.cursor.execute('''
                SELECT key, value FROM config ORDER BY key
            ''')
            
            for row in self.db.cursor.fetchall():
                key = row['key']
                value = row['value']
                
                # 尝试解析JSON格式的值
                try:
                    configs[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    configs[key] = value
            
        except sqlite3.Error as e:
            print(f"获取所有配置失败: {e}")
        
        return configs
    
    def delete_config(self, key: str) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置键
            
        Returns:
            是否删除成功
        """
        try:
            self.db.cursor.execute('''
                DELETE FROM config WHERE key = ?
            ''', (key,))
            
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"删除配置失败: {e}")
            return False
    
    def config_exists(self, key: str) -> bool:
        """
        检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            是否存在
        """
        try:
            self.db.cursor.execute('''
                SELECT 1 FROM config WHERE key = ?
            ''', (key,))
            
            return self.db.cursor.fetchone() is not None
            
        except sqlite3.Error as e:
            print(f"检查配置存在性失败: {e}")
            return False
    
    def get_config_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取配置及其元数据
        
        Args:
            key: 配置键
            
        Returns:
            包含值和元数据的字典，不存在返回None
        """
        try:
            self.db.cursor.execute('''
                SELECT key, value, updated_at FROM config WHERE key = ?
            ''', (key,))
            
            result = self.db.cursor.fetchone()
            if result:
                value = result['value']
                # 尝试解析JSON格式的值
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_value = value
                
                return {
                    'key': result['key'],
                    'value': parsed_value,
                    'raw_value': value,
                    'updated_at': result['updated_at']
                }
            return None
            
        except sqlite3.Error as e:
            print(f"获取配置元数据失败: {e}")
            return None
    
    def search_configs(self, pattern: str) -> List[Dict[str, Any]]:
        """
        搜索配置项
        
        Args:
            pattern: 搜索模式（支持SQL LIKE语法）
            
        Returns:
            匹配的配置列表
        """
        configs = []
        try:
            self.db.cursor.execute('''
                SELECT key, value, updated_at FROM config 
                WHERE key LIKE ? 
                ORDER BY key
            ''', (pattern,))
            
            for row in self.db.cursor.fetchall():
                value = row['value']
                # 尝试解析JSON格式的值
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_value = value
                
                configs.append({
                    'key': row['key'],
                    'value': parsed_value,
                    'raw_value': value,
                    'updated_at': row['updated_at']
                })
            
        except sqlite3.Error as e:
            print(f"搜索配置失败: {e}")
        
        return configs
    
    def get_config_count(self) -> int:
        """
        获取配置项总数
        
        Returns:
            配置项总数
        """
        try:
            self.db.cursor.execute('''
                SELECT COUNT(*) as count FROM config
            ''')
            result = self.db.cursor.fetchone()
            return result['count'] if result else 0
            
        except sqlite3.Error as e:
            print(f"获取配置总数失败: {e}")
            return 0
    
    def backup_configs(self) -> Dict[str, Any]:
        """
        备份所有配置
        
        Returns:
            配置备份字典
        """
        backup = {
            'timestamp': datetime.now().isoformat(),
            'configs': self.get_all_configs()
        }
        return backup
    
    def restore_configs(self, backup: Dict[str, Any]) -> bool:
        """
        从备份恢复配置
        
        Args:
            backup: 配置备份字典
            
        Returns:
            是否恢复成功
        """
        try:
            if 'configs' not in backup:
                print("无效的备份格式")
                return False
            
            # 开始事务
            self.db.cursor.execute('BEGIN TRANSACTION')
            
            # 清空现有配置（可选，根据需求决定）
            # self.db.cursor.execute('DELETE FROM config')
            
            # 恢复配置
            success_count = 0
            for key, value in backup['configs'].items():
                if self.set_config(key, value):
                    success_count += 1
            
            self.db.connection.commit()
            print(f"成功恢复 {success_count} 个配置项")
            return True
            
        except sqlite3.Error as e:
            print(f"恢复配置失败: {e}")
            if self.db.connection:
                self.db.connection.rollback()
            return False
    
    # 便捷方法：常用配置的快捷访问
    def get_photo_library_path(self) -> str:
        """获取照片库路径"""
        return self.get_config('photo_library_path', '')
    
    def set_photo_library_path(self, path: str) -> bool:
        """设置照片库路径"""
        return self.set_config('photo_library_path', path)
    
    def get_last_import_path(self) -> str:
        """获取上次导入路径"""
        return self.get_config('last_import_path', '')
    
    def set_last_import_path(self, path: str) -> bool:
        """设置上次导入路径"""
        return self.set_config('last_import_path', path)
    
    def get_window_geometry(self) -> Dict[str, int]:
        """获取窗口几何信息"""
        return self.get_config('window_geometry', {'width': 1200, 'height': 800, 'x': 100, 'y': 100})
    
    def set_window_geometry(self, geometry: Dict[str, int]) -> bool:
        """设置窗口几何信息"""
        return self.set_config('window_geometry', geometry)
    
    def get_thumbnail_size(self) -> int:
        """获取缩略图大小"""
        return self.get_config('thumbnail_size', 200)
    
    def set_thumbnail_size(self, size: int) -> bool:
        """设置缩略图大小"""
        return self.set_config('thumbnail_size', size)