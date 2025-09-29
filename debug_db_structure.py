#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查.library.db数据库的表结构
"""

import os
import sqlite3
from pathlib import Path

def check_database_structure():
    """检查数据库结构"""
    project_root = Path(__file__).parent
    db_path = os.path.join(project_root, "myphotolib/.library.db")
    
    print(f"🔍 检查数据库结构")
    print(f"数据库路径: {db_path}")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 获取所有表名
        print("1️⃣ 获取所有表名...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"   📋 {table[0]}")
        else:
            print("❌ 未找到任何表")
            return False
        
        # 2. 检查每个表的结构
        print(f"\n2️⃣ 检查表结构...")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 表: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            if columns:
                print(f"   列数: {len(columns)}")
                for col in columns:
                    cid, name, type_, notnull, default, pk = col
                    print(f"   - {name} ({type_}){' [主键]' if pk else ''}{' [非空]' if notnull else ''}")
            
            # 获取表中的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   记录数: {count}")
            
            # 如果是照片相关的表，显示一些示例数据
            if any(keyword in table_name.lower() for keyword in ['photo', 'image', 'pic']):
                print(f"   📸 照片相关表，显示前3条记录:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"     记录{i}: {row[:5]}...")  # 只显示前5个字段
        
        # 3. 查找包含GPS或EXIF信息的表
        print(f"\n3️⃣ 查找包含GPS/EXIF信息的表...")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            gps_columns = []
            exif_columns = []
            
            for col in columns:
                col_name = col[1].lower()
                if 'gps' in col_name:
                    gps_columns.append(col[1])
                if 'exif' in col_name:
                    exif_columns.append(col[1])
            
            if gps_columns or exif_columns:
                print(f"   📋 {table_name}:")
                if gps_columns:
                    print(f"     GPS列: {', '.join(gps_columns)}")
                if exif_columns:
                    print(f"     EXIF列: {', '.join(exif_columns)}")
        
        # 4. 查找包含特定文件名的记录
        print(f"\n4️⃣ 查找包含 'IMG_20250819_094620.jpg' 的记录...")
        target_filename = "IMG_20250819_094620.jpg"
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # 查找可能包含文件名的列
            filename_columns = []
            for col in columns:
                col_name = col[1].lower()
                if any(keyword in col_name for keyword in ['name', 'file', 'path']):
                    filename_columns.append(col[1])
            
            if filename_columns:
                for col_name in filename_columns:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE {col_name} LIKE ?", (f"%{target_filename}%",))
                        matches = cursor.fetchall()
                        if matches:
                            print(f"   ✅ 在表 {table_name} 的列 {col_name} 中找到 {len(matches)} 条匹配记录")
                            for i, match in enumerate(matches[:2], 1):  # 只显示前2条
                                print(f"     记录{i}: {match[:3]}...")
                    except Exception as e:
                        print(f"   ⚠️ 查询表 {table_name} 列 {col_name} 时出错: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查数据库结构时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 数据库结构检查")
    print("=" * 60)
    
    success = check_database_structure()
    
    if success:
        print("\n✅ 检查完成")
    else:
        print("\n❌ 检查失败")