#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAO管理器
提供统一的数据库访问接口，整合PhotoDAO和ConfigDAO
"""

import os
from typing import Optional, Dict, List, Any
from .database import Database
from .photo_dao import PhotoDAO
from .config_dao import ConfigDAO


class DAOManager:
    """DAO管理器，提供统一的数据库访问接口"""
    
    def __init__(self, db_path: str):
        """
        初始化DAO管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.database = Database(db_path)
        self.photo_dao = PhotoDAO(self.database)
        self.config_dao = ConfigDAO(self.database)
        self._connected = False
    
    def initialize(self) -> bool:
        """
        初始化数据库连接和表结构
        
        Returns:
            是否初始化成功
        """
        if not self.database.connect():
            return False
        
        if not self.database.initialize():
            return False
        
        self._connected = True
        return True
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.database:
            self.database.close()
        self._connected = False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    # === 照片相关操作 ===
    
    def add_photo(self, 
                 filename: str,
                 path: str,
                 md5: str,
                 size: int,
                 created_at: Optional[str] = None,
                 photo_type: str = "jpg",
                 exif_data: Optional[Dict] = None,
                 thumbnail_path: Optional[str] = None) -> Optional[int]:
        """
        添加照片记录
        
        Args:
            filename: 文件名
            path: 文件路径（相对于照片库）
            md5: 文件MD5值
            size: 文件大小（字节）
            created_at: 照片创建时间（ISO格式）
            photo_type: 照片类型
            exif_data: EXIF数据字典
            thumbnail_path: 缩略图路径
            
        Returns:
            照片ID，失败返回None
        """
        return self.photo_dao.insert_photo(
            filename, path, md5, size, created_at, 
            photo_type, exif_data, thumbnail_path
        )
    
    def get_photo_by_id(self, photo_id: int) -> Optional[Dict]:
        """根据ID获取照片信息"""
        return self.photo_dao.get_photo_by_id(photo_id)
    
    def get_recent_photos(self, limit: int = 20) -> List[Dict]:
        """获取最近导入的照片"""
        return self.photo_dao.get_recent_photos(limit)
    
    def search_photos(self, 
                     filename_pattern: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     photo_type: Optional[str] = None,
                     md5: Optional[str] = None,
                     limit: int = 100) -> List[Dict]:
        """
        多条件搜索照片
        
        Args:
            filename_pattern: 文件名模式（支持SQL LIKE语法）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            photo_type: 照片类型
            md5: MD5值（精确匹配）
            limit: 返回数量限制
            
        Returns:
            照片列表
        """
        # 如果指定了MD5，直接查找
        if md5:
            photo = self.photo_dao.get_photo_by_md5(md5, 0)  # size=0表示忽略大小
            return [photo] if photo else []
        
        # 构建复合查询
        conditions = ["is_deleted = 0"]
        params = []
        
        if filename_pattern:
            conditions.append("filename LIKE ?")
            params.append(filename_pattern)
        
        if start_date and end_date:
            conditions.append("DATE(created_at) BETWEEN ? AND ?")
            params.extend([start_date, end_date])
        elif start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        elif end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)
        
        if photo_type:
            conditions.append("type = ?")
            params.append(photo_type)
        
        params.append(limit)
        
        try:
            sql = f'''
                SELECT * FROM photos 
                WHERE {' AND '.join(conditions)}
                ORDER BY imported_at DESC 
                LIMIT ?
            '''
            
            self.database.cursor.execute(sql, params)
            
            photos = []
            for row in self.database.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    import json
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except Exception as e:
            print(f"搜索照片失败: {e}")
            return []
    
    def photo_exists(self, md5: str, size: int) -> bool:
        """检查照片是否已存在"""
        return self.photo_dao.photo_exists(md5, size)
    
    def get_photos_stats(self) -> Dict[str, Any]:
        """获取照片统计信息"""
        return self.photo_dao.get_photos_stats()
    
    def update_photo(self, photo_id: int, updates: Dict[str, Any]) -> bool:
        """更新照片信息"""
        return self.photo_dao.update_photo(photo_id, updates)
    
    def delete_photo(self, photo_id: int, soft_delete: bool = True) -> bool:
        """删除照片"""
        return self.photo_dao.delete_photo(photo_id, soft_delete)
    
    # === 配置相关操作 ===
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_dao.get_config(key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值"""
        return self.config_dao.set_config(key, value)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_dao.get_all_configs()
    
    def delete_config(self, key: str) -> bool:
        """删除配置项"""
        return self.config_dao.delete_config(key)
    
    # === 便捷方法 ===
    
    def get_photo_library_path(self) -> str:
        """获取照片库路径"""
        return self.config_dao.get_photo_library_path()
    
    def set_photo_library_path(self, path: str) -> bool:
        """设置照片库路径"""
        return self.config_dao.set_photo_library_path(path)
    
    def get_last_import_path(self) -> str:
        """获取上次导入路径"""
        return self.config_dao.get_last_import_path()
    
    def set_last_import_path(self, path: str) -> bool:
        """设置上次导入路径"""
        return self.config_dao.set_last_import_path(path)
    
    # === 高级查询接口 ===
    
    def get_photos_by_date(self, date: str) -> List[Dict]:
        """
        获取指定日期的照片
        
        Args:
            date: 日期（YYYY-MM-DD）
            
        Returns:
            照片列表
        """
        return self.search_photos(start_date=date, end_date=date)
    
    def get_photos_by_month(self, year: int, month: int) -> List[Dict]:
        """
        获取指定月份的照片
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            照片列表
        """
        start_date = f"{year:04d}-{month:02d}-01"
        
        # 计算月末日期
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1
        
        from datetime import datetime, timedelta
        next_month_start = datetime(next_year, next_month, 1)
        month_end = next_month_start - timedelta(days=1)
        end_date = month_end.strftime("%Y-%m-%d")
        
        return self.search_photos(start_date=start_date, end_date=end_date)
    
    def get_photos_by_year(self, year: int) -> List[Dict]:
        """
        获取指定年份的照片
        
        Args:
            year: 年份
            
        Returns:
            照片列表
        """
        start_date = f"{year:04d}-01-01"
        end_date = f"{year:04d}-12-31"
        return self.search_photos(start_date=start_date, end_date=end_date)
    
    def get_duplicate_photos(self) -> List[List[Dict]]:
        """
        获取重复照片（相同MD5和大小）
        
        Returns:
            重复照片组列表
        """
        try:
            # 查找重复的MD5和大小组合
            self.database.cursor.execute('''
                SELECT md5, size, COUNT(*) as count
                FROM photos 
                WHERE is_deleted = 0
                GROUP BY md5, size
                HAVING count > 1
            ''')
            
            duplicate_groups = []
            for row in self.database.cursor.fetchall():
                md5, size = row['md5'], row['size']
                
                # 获取该组的所有照片
                self.database.cursor.execute('''
                    SELECT * FROM photos 
                    WHERE md5 = ? AND size = ? AND is_deleted = 0
                    ORDER BY imported_at
                ''', (md5, size))
                
                group_photos = []
                for photo_row in self.database.cursor.fetchall():
                    photo = dict(photo_row)
                    if photo['exif_json']:
                        import json
                        try:
                            photo['exif_data'] = json.loads(photo['exif_json'])
                        except json.JSONDecodeError:
                            photo['exif_data'] = {}
                    else:
                        photo['exif_data'] = {}
                    group_photos.append(photo)
                
                if len(group_photos) > 1:
                    duplicate_groups.append(group_photos)
            
            return duplicate_groups
            
        except Exception as e:
            print(f"获取重复照片失败: {e}")
            return []
    
    def get_photos_without_thumbnails(self) -> List[Dict]:
        """
        获取没有缩略图的照片
        
        Returns:
            照片列表
        """
        try:
            self.database.cursor.execute('''
                SELECT * FROM photos 
                WHERE (thumbnail_path IS NULL OR thumbnail_path = '') 
                AND is_deleted = 0
                ORDER BY imported_at DESC
            ''')
            
            photos = []
            for row in self.database.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    import json
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except Exception as e:
            print(f"获取无缩略图照片失败: {e}")
            return []
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self.initialize():
            raise Exception("数据库初始化失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()