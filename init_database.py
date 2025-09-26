#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据库并添加测试数据
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.dao_manager import DAOManager

def init_database():
    """初始化数据库"""
    db_path = "./db/photos.db"
    
    # 确保 db 目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 初始化 DAO 管理器
    dao_manager = DAOManager(db_path)
    
    if not dao_manager.initialize():
        print("数据库初始化失败")
        return False
    
    print(f"数据库初始化成功: {db_path}")
    
    # 添加一些测试照片数据
    test_photos = [
        {
            "filename": "IMG_001.jpg",
            "path": "d:/dele-1/mypm/myphotolib/2025/08/14/IMG_001.jpg",
            "md5": "test_md5_001",
            "size": 1024000,
            "photo_type": "jpg",
            "created_at": "2025-08-14 10:30:00"
        },
        {
            "filename": "IMG_002.jpg", 
            "path": "d:/dele-1/mypm/myphotolib/2025/08/14/IMG_002.jpg",
            "md5": "test_md5_002",
            "size": 2048000,
            "photo_type": "jpg",
            "created_at": "2025-08-14 11:15:00"
        },
        {
            "filename": "IMG_003.png",
            "path": "d:/dele-1/mypm/myphotolib/2025/08/14/IMG_003.png", 
            "md5": "test_md5_003",
            "size": 1536000,
            "photo_type": "png",
            "created_at": "2025-08-14 12:00:00"
        }
    ]
    
    # 插入测试数据
    for photo in test_photos:
        photo_id = dao_manager.add_photo(
            filename=photo["filename"],
            path=photo["path"],
            md5=photo["md5"],
            size=photo["size"],
            photo_type=photo["photo_type"],
            created_at=photo["created_at"]
        )
        if photo_id:
            print(f"添加照片成功: {photo['filename']} (ID: {photo_id})")
        else:
            print(f"添加照片失败: {photo['filename']}")
    
    # 验证数据
    recent_photos = dao_manager.get_recent_photos(10)
    print(f"\n数据库中共有 {len(recent_photos)} 张照片:")
    for photo in recent_photos:
        print(f"  ID: {photo['id']}, 文件名: {photo['filename']}, 路径: {photo['path']}")
    
    dao_manager.close()
    return True

if __name__ == "__main__":
    init_database()