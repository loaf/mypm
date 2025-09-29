#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_table_schema():
    """检查photos表的确切结构"""
    db_path = "myphotolib/.library.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取photos表的结构
        cursor.execute("PRAGMA table_info(photos)")
        columns = cursor.fetchall()
        
        print("📋 photos表的列结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'[主键]' if col[5] else ''} {'[非空]' if col[3] else ''}")
        
        # 查询特定照片
        cursor.execute("SELECT * FROM photos WHERE filename LIKE ?", ("%IMG_20250819_094620.jpg%",))
        result = cursor.fetchone()
        
        if result:
            print(f"\n📸 找到照片记录:")
            for i, col in enumerate(columns):
                value = result[i] if i < len(result) else "N/A"
                if col[1] == 'exif_json' and value:
                    print(f"  {col[1]}: {value[:100]}..." if len(str(value)) > 100 else f"  {col[1]}: {value}")
                else:
                    print(f"  {col[1]}: {value}")
        else:
            print("\n❌ 未找到指定照片")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_table_schema()