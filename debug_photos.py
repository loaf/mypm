#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from db.dao_manager import DAOManager

def check_photos():
    dao = DAOManager()
    dao.initialize()
    
    # 检查最近照片
    photos = dao.get_recent_photos(10)
    print(f"数据库中共有 {len(photos)} 张最近照片")
    
    for i, photo in enumerate(photos):
        print(f"{i+1}. ID: {photo['id']}, 文件名: {photo['filename']}, 路径: {photo['path']}")
    
    # 测试按目录查询
    if photos:
        test_path = photos[0]['path']
        print(f"\n测试路径: {test_path}")
        
        # 提取目录部分
        import os
        directory = os.path.dirname(test_path)
        print(f"目录: {directory}")
        
        # 测试查询
        dir_photos = dao.photo_dao.get_photos_by_directory(directory)
        print(f"按目录查询结果: {len(dir_photos)} 张照片")
        
        for photo in dir_photos:
            print(f"  - {photo['filename']} ({photo['path']})")
    
    dao.close()

if __name__ == "__main__":
    check_photos()