"""
数据库管理器 - 专门处理照片导入相关的数据库操作
"""

import sqlite3
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import json
from .database import Database


class DatabaseManager:
    """数据库管理器，专门处理照片导入功能"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.database = Database(db_path)
        
    def connect(self) -> bool:
        """连接数据库"""
        return self.database.connect()
    
    def initialize(self) -> bool:
        """初始化数据库"""
        return self.database.initialize()
    
    def photo_exists_by_hash(self, md5: str, size: int) -> bool:
        """
        通过MD5和文件大小检查照片是否已存在
        
        Args:
            md5: 文件MD5值
            size: 文件大小（字节）
            
        Returns:
            bool: 照片是否已存在
        """
        return self.database.photo_exists(md5, size)
    
    def add_photo_record(self, 
                        filename: str,
                        relative_path: str,
                        md5: str,
                        size: int,
                        created_at: str,
                        photo_type: str = "jpg",
                        exif_data: Optional[Dict] = None,
                        thumbnail_path: Optional[str] = None) -> Optional[int]:
        """
        添加照片记录到数据库
        
        Args:
            filename: 文件名
            relative_path: 相对于照片库的路径
            md5: 文件MD5值
            size: 文件大小
            created_at: 照片创建时间（ISO格式）
            photo_type: 照片类型
            exif_data: EXIF数据字典
            thumbnail_path: 缩略图路径
            
        Returns:
            int: 照片ID，失败返回None
        """
        photo_data = {
            'filename': filename,
            'path': relative_path,
            'md5': md5,
            'size': size,
            'created_at': created_at,
            'imported_at': datetime.now().isoformat(),
            'type': photo_type,
            'exif_json': json.dumps(exif_data) if exif_data else None,
            'thumbnail_path': thumbnail_path
        }
        
        return self.database.add_photo(photo_data)
    
    def get_photos_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取指定日期范围内的照片
        
        Args:
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            
        Returns:
            List[Dict]: 照片记录列表
        """
        try:
            self.database.cursor.execute('''
                SELECT * FROM photos 
                WHERE DATE(created_at) BETWEEN ? AND ? 
                AND is_deleted = 0
                ORDER BY created_at DESC
            ''', (start_date, end_date))
            
            columns = [description[0] for description in self.database.cursor.description]
            return [dict(zip(columns, row)) for row in self.database.cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"查询照片失败: {e}")
            return []
    
    def get_photos_by_month(self, year: int, month: int) -> List[Dict]:
        """
        获取指定月份的照片
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            List[Dict]: 照片记录列表
        """
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
            
        try:
            self.database.cursor.execute('''
                SELECT * FROM photos 
                WHERE created_at >= ? AND created_at < ? 
                AND is_deleted = 0
                ORDER BY created_at DESC
            ''', (start_date, end_date))
            
            columns = [description[0] for description in self.database.cursor.description]
            return [dict(zip(columns, row)) for row in self.database.cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"查询月份照片失败: {e}")
            return []
    
    def get_duplicate_photos(self) -> List[Tuple[str, int, List[Dict]]]:
        """
        获取重复的照片（相同MD5和大小）
        
        Returns:
            List[Tuple]: (md5, size, photos_list) 的列表
        """
        try:
            self.database.cursor.execute('''
                SELECT md5, size, COUNT(*) as count
                FROM photos 
                WHERE is_deleted = 0
                GROUP BY md5, size
                HAVING count > 1
            ''')
            
            duplicates = []
            for row in self.database.cursor.fetchall():
                md5, size, count = row
                
                # 获取具有相同MD5和大小的所有照片
                self.database.cursor.execute('''
                    SELECT * FROM photos 
                    WHERE md5 = ? AND size = ? AND is_deleted = 0
                    ORDER BY imported_at
                ''', (md5, size))
                
                columns = [description[0] for description in self.database.cursor.description]
                photos = [dict(zip(columns, photo_row)) for photo_row in self.database.cursor.fetchall()]
                
                duplicates.append((md5, size, photos))
            
            return duplicates
            
        except sqlite3.Error as e:
            print(f"查询重复照片失败: {e}")
            return []
    
    def update_photo_thumbnail(self, photo_id: int, thumbnail_path: str) -> bool:
        """
        更新照片的缩略图路径
        
        Args:
            photo_id: 照片ID
            thumbnail_path: 缩略图路径
            
        Returns:
            bool: 是否更新成功
        """
        try:
            self.database.cursor.execute('''
                UPDATE photos 
                SET thumbnail_path = ?, updated_at = ?
                WHERE id = ?
            ''', (thumbnail_path, datetime.now().isoformat(), photo_id))
            
            self.database.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"更新缩略图失败: {e}")
            return False
    
    def delete_photo_record(self, photo_id: int) -> bool:
        """
        删除照片记录（软删除）
        
        Args:
            photo_id: 照片ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self.database.cursor.execute('''
                UPDATE photos 
                SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), photo_id))
            
            self.database.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"删除照片记录失败: {e}")
            return False
    
    def get_library_statistics(self) -> Dict[str, Any]:
        """
        获取照片库统计信息
        
        Returns:
            Dict: 统计信息
        """
        return self.database.get_library_stats()
    
    def get_all_photos(self):
        """获取所有照片记录"""
        try:
            if not self.database.cursor:
                self.connect()
                
            self.database.cursor.execute('''
                SELECT id, filename, md5, size, created_at, path as relative_path, type as photo_type
                FROM photos
                WHERE is_deleted = 0
                ORDER BY created_at DESC
            ''')
            
            columns = [description[0] for description in self.database.cursor.description]
            return [dict(zip(columns, row)) for row in self.database.cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"查询所有照片失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        self.database.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()