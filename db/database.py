#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库操作模块
负责SQLite数据库的创建、连接和基本操作
"""

import sqlite3
import os
from typing import Optional, Dict, List, Any
from datetime import datetime


class Database:
    """数据库操作类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
    
    def connect(self) -> bool:
        """
        连接数据库
        
        Returns:
            是否连接成功
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问
            self.cursor = self.connection.cursor()
            
            # 启用外键约束
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            return True
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def initialize(self) -> bool:
        """
        初始化数据库表结构
        
        Returns:
            是否初始化成功
        """
        if not self.connect():
            return False
        
        try:
            # 创建照片表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    md5 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_at TEXT,
                    imported_at TEXT NOT NULL,
                    type TEXT NOT NULL,
                    exif_json TEXT,
                    thumbnail_path TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    UNIQUE(md5, size)
                )
            ''')
            
            # 创建配置表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 创建标签表（为将来扩展预留）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#007ACC',
                    created_at TEXT NOT NULL
                )
            ''')
            
            # 创建照片标签关联表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS photo_tags (
                    photo_id INTEGER,
                    tag_id INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (photo_id, tag_id),
                    FOREIGN KEY (photo_id) REFERENCES photos (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            ''')
            
            # 创建相册表（为将来扩展预留）
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    cover_photo_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (cover_photo_id) REFERENCES photos (id)
                )
            ''')
            
            # 创建相册照片关联表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS album_photos (
                    album_id INTEGER,
                    photo_id INTEGER,
                    added_at TEXT NOT NULL,
                    PRIMARY KEY (album_id, photo_id),
                    FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE CASCADE,
                    FOREIGN KEY (photo_id) REFERENCES photos (id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引以提高查询性能
            self._create_indexes()
            
            # 插入初始配置
            self._insert_initial_config()
            
            self.connection.commit()
            print("数据库初始化完成")
            return True
            
        except sqlite3.Error as e:
            print(f"数据库初始化失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _create_indexes(self) -> None:
        """创建数据库索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_photos_md5 ON photos(md5)",
            "CREATE INDEX IF NOT EXISTS idx_photos_created_at ON photos(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_photos_type ON photos(type)",
            "CREATE INDEX IF NOT EXISTS idx_photos_is_deleted ON photos(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_config_key ON config(key)"
        ]
        
        for index_sql in indexes:
            self.cursor.execute(index_sql)
    
    def _insert_initial_config(self) -> None:
        """插入初始配置"""
        initial_configs = [
            ("db_version", "1.0.0"),
            ("created_at", datetime.now().isoformat()),
            ("last_backup", ""),
            ("photo_count", "0")
        ]
        
        for key, value in initial_configs:
            self.cursor.execute('''
                INSERT OR IGNORE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
    
    def get_config(self, key: str, default: str = "") -> str:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            self.cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result['value'] if result else default
        except sqlite3.Error as e:
            print(f"获取配置失败: {e}")
            return default
    
    def set_config(self, key: str, value: str) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"设置配置失败: {e}")
            return False
    
    def add_photo(self, photo_data: Dict[str, Any]) -> Optional[int]:
        """
        添加照片记录
        
        Args:
            photo_data: 照片数据字典
            
        Returns:
            照片ID，失败返回None
        """
        try:
            self.cursor.execute('''
                INSERT INTO photos (
                    filename, path, md5, size, created_at, imported_at,
                    type, exif_json, thumbnail_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                photo_data['filename'],
                photo_data['path'],
                photo_data['md5'],
                photo_data['size'],
                photo_data.get('created_at'),
                photo_data['imported_at'],
                photo_data['type'],
                photo_data.get('exif_json'),
                photo_data.get('thumbnail_path')
            ))
            
            photo_id = self.cursor.lastrowid
            self.connection.commit()
            
            # 更新照片计数
            self._update_photo_count()
            
            return photo_id
            
        except sqlite3.IntegrityError:
            # 重复照片
            print(f"照片已存在: {photo_data['path']}")
            return None
        except sqlite3.Error as e:
            print(f"添加照片失败: {e}")
            return None
    
    def photo_exists(self, md5: str, size: int) -> bool:
        """
        检查照片是否已存在
        
        Args:
            md5: 文件MD5值
            size: 文件大小
            
        Returns:
            是否存在
        """
        try:
            self.cursor.execute(
                "SELECT id FROM photos WHERE md5 = ? AND size = ? AND is_deleted = 0",
                (md5, size)
            )
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"检查照片存在性失败: {e}")
            return False
    
    def get_library_stats(self) -> Dict[str, Any]:
        """
        获取照片库统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "photos_count": 0,
            "total_size": 0,
            "types_count": {},
            "latest_import": None
        }
        
        try:
            # 照片总数
            self.cursor.execute("SELECT COUNT(*) as count FROM photos WHERE is_deleted = 0")
            result = self.cursor.fetchone()
            stats["photos_count"] = result['count'] if result else 0
            
            # 总大小
            self.cursor.execute("SELECT SUM(size) as total_size FROM photos WHERE is_deleted = 0")
            result = self.cursor.fetchone()
            stats["total_size"] = result['total_size'] if result and result['total_size'] else 0
            
            # 按类型统计
            self.cursor.execute('''
                SELECT type, COUNT(*) as count 
                FROM photos 
                WHERE is_deleted = 0 
                GROUP BY type
            ''')
            for row in self.cursor.fetchall():
                stats["types_count"][row['type']] = row['count']
            
            # 最新导入时间
            self.cursor.execute('''
                SELECT MAX(imported_at) as latest 
                FROM photos 
                WHERE is_deleted = 0
            ''')
            result = self.cursor.fetchone()
            stats["latest_import"] = result['latest'] if result else None
            
        except sqlite3.Error as e:
            print(f"获取统计信息失败: {e}")
        
        return stats
    
    def _update_photo_count(self) -> None:
        """更新照片计数配置"""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM photos WHERE is_deleted = 0")
            result = self.cursor.fetchone()
            count = result['count'] if result else 0
            self.set_config("photo_count", str(count))
        except sqlite3.Error as e:
            print(f"更新照片计数失败: {e}")
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """析构函数"""
        self.close()