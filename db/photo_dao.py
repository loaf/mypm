#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照片数据访问对象 (Photo DAO)
封装照片相关的数据库操作，提供清晰的接口
"""

import sqlite3
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from .database import Database


class PhotoDAO:
    """照片数据访问对象"""
    
    def __init__(self, database: Database):
        """
        初始化PhotoDAO
        
        Args:
            database: 数据库实例
        """
        self.db = database
    
    def insert_photo(self, 
                    filename: str,
                    path: str,
                    md5: str,
                    size: int,
                    created_at: Optional[str] = None,
                    photo_type: str = "jpg",
                    exif_data: Optional[Dict] = None,
                    thumbnail_path: Optional[str] = None) -> Optional[int]:
        """
        插入照片记录
        
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
        photo_data = {
            'filename': filename,
            'path': path,
            'md5': md5,
            'size': size,
            'created_at': created_at,
            'imported_at': datetime.now().isoformat(),
            'type': photo_type,
            'exif_json': json.dumps(exif_data, ensure_ascii=False) if exif_data else None,
            'thumbnail_path': thumbnail_path
        }
        
        return self.db.add_photo(photo_data)
    
    def get_photo_by_id(self, photo_id: int) -> Optional[Dict]:
        """
        根据ID获取照片信息
        
        Args:
            photo_id: 照片ID
            
        Returns:
            照片信息字典，不存在返回None
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE id = ? AND is_deleted = 0
            ''', (photo_id,))
            
            row = self.db.cursor.fetchone()
            if row:
                photo = dict(row)
                # 解析EXIF JSON数据
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                return photo
            return None
            
        except sqlite3.Error as e:
            print(f"获取照片失败: {e}")
            return None
    
    def get_photo_by_md5(self, md5: str, size: int) -> Optional[Dict]:
        """
        根据MD5和大小获取照片信息
        
        Args:
            md5: 文件MD5值
            size: 文件大小
            
        Returns:
            照片信息字典，不存在返回None
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE md5 = ? AND size = ? AND is_deleted = 0
            ''', (md5, size))
            
            row = self.db.cursor.fetchone()
            if row:
                photo = dict(row)
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                return photo
            return None
            
        except sqlite3.Error as e:
            print(f"获取照片失败: {e}")
            return None
    
    def get_recent_photos(self, limit: int = 20) -> List[Dict]:
        """
        获取最近导入的照片
        
        Args:
            limit: 返回数量限制
            
        Returns:
            照片列表
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE is_deleted = 0 
                ORDER BY imported_at DESC 
                LIMIT ?
            ''', (limit,))
            
            photos = []
            for row in self.db.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except sqlite3.Error as e:
            print(f"获取最近照片失败: {e}")
            return []
    
    def get_photos_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取指定日期范围内的照片
        
        Args:
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            
        Returns:
            照片列表
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE DATE(created_at) BETWEEN ? AND ? 
                AND is_deleted = 0
                ORDER BY created_at DESC
            ''', (start_date, end_date))
            
            photos = []
            for row in self.db.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except sqlite3.Error as e:
            print(f"按日期范围获取照片失败: {e}")
            return []
    
    def search_photos_by_filename(self, filename_pattern: str) -> List[Dict]:
        """
        根据文件名模式搜索照片
        
        Args:
            filename_pattern: 文件名模式（支持SQL LIKE语法）
            
        Returns:
            照片列表
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE filename LIKE ? AND is_deleted = 0
                ORDER BY imported_at DESC
            ''', (filename_pattern,))
            
            photos = []
            for row in self.db.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except sqlite3.Error as e:
            print(f"按文件名搜索照片失败: {e}")
            return []
    
    def get_photos_by_type(self, photo_type: str) -> List[Dict]:
        """
        根据照片类型获取照片
        
        Args:
            photo_type: 照片类型（如 jpg, png, raw等）
            
        Returns:
            照片列表
        """
        try:
            self.db.cursor.execute('''
                SELECT * FROM photos 
                WHERE type = ? AND is_deleted = 0
                ORDER BY imported_at DESC
            ''', (photo_type,))
            
            photos = []
            for row in self.db.cursor.fetchall():
                photo = dict(row)
                if photo['exif_json']:
                    try:
                        photo['exif_data'] = json.loads(photo['exif_json'])
                    except json.JSONDecodeError:
                        photo['exif_data'] = {}
                else:
                    photo['exif_data'] = {}
                photos.append(photo)
            
            return photos
            
        except sqlite3.Error as e:
            print(f"按类型获取照片失败: {e}")
            return []
    
    def update_photo(self, photo_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新照片信息
        
        Args:
            photo_id: 照片ID
            updates: 要更新的字段字典
            
        Returns:
            是否更新成功
        """
        if not updates:
            return True
        
        try:
            # 构建更新SQL
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key == 'exif_data':
                    # 特殊处理EXIF数据
                    set_clauses.append('exif_json = ?')
                    values.append(json.dumps(value, ensure_ascii=False) if value else None)
                elif key in ['filename', 'path', 'thumbnail_path', 'type']:
                    set_clauses.append(f'{key} = ?')
                    values.append(value)
            
            if not set_clauses:
                return True
            
            values.append(photo_id)
            sql = f"UPDATE photos SET {', '.join(set_clauses)} WHERE id = ?"
            
            self.db.cursor.execute(sql, values)
            self.db.connection.commit()
            
            return self.db.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"更新照片失败: {e}")
            return False
    
    def delete_photo(self, photo_id: int, soft_delete: bool = True) -> bool:
        """
        删除照片（支持软删除和硬删除）
        
        Args:
            photo_id: 照片ID
            soft_delete: 是否软删除（标记为删除而不是真正删除）
            
        Returns:
            是否删除成功
        """
        try:
            if soft_delete:
                # 软删除：标记为已删除
                self.db.cursor.execute('''
                    UPDATE photos SET is_deleted = 1 WHERE id = ?
                ''', (photo_id,))
            else:
                # 硬删除：真正删除记录
                self.db.cursor.execute('''
                    DELETE FROM photos WHERE id = ?
                ''', (photo_id,))
            
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"删除照片失败: {e}")
            return False
    
    def get_photo_count(self) -> int:
        """
        获取照片总数
        
        Returns:
            照片总数
        """
        try:
            self.db.cursor.execute('''
                SELECT COUNT(*) as count FROM photos WHERE is_deleted = 0
            ''')
            result = self.db.cursor.fetchone()
            return result['count'] if result else 0
            
        except sqlite3.Error as e:
            print(f"获取照片总数失败: {e}")
            return 0
    
    def get_photos_stats(self) -> Dict[str, Any]:
        """
        获取照片统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_count": 0,
            "total_size": 0,
            "type_distribution": {},
            "latest_import": None,
            "oldest_photo": None
        }
        
        try:
            # 总数和总大小
            self.db.cursor.execute('''
                SELECT COUNT(*) as count, SUM(size) as total_size 
                FROM photos WHERE is_deleted = 0
            ''')
            result = self.db.cursor.fetchone()
            if result:
                stats["total_count"] = result['count'] or 0
                stats["total_size"] = result['total_size'] or 0
            
            # 按类型分布
            self.db.cursor.execute('''
                SELECT type, COUNT(*) as count 
                FROM photos WHERE is_deleted = 0 
                GROUP BY type
            ''')
            for row in self.db.cursor.fetchall():
                stats["type_distribution"][row['type']] = row['count']
            
            # 最新导入时间
            self.db.cursor.execute('''
                SELECT MAX(imported_at) as latest 
                FROM photos WHERE is_deleted = 0
            ''')
            result = self.db.cursor.fetchone()
            if result:
                stats["latest_import"] = result['latest']
            
            # 最早照片时间
            self.db.cursor.execute('''
                SELECT MIN(created_at) as oldest 
                FROM photos WHERE is_deleted = 0 AND created_at IS NOT NULL
            ''')
            result = self.db.cursor.fetchone()
            if result:
                stats["oldest_photo"] = result['oldest']
            
        except sqlite3.Error as e:
            print(f"获取照片统计失败: {e}")
        
        return stats
    
    def photo_exists(self, md5: str, size: int) -> bool:
        """
        检查照片是否已存在
        
        Args:
            md5: 文件MD5值
            size: 文件大小
            
        Returns:
            是否存在
        """
        return self.db.photo_exists(md5, size)