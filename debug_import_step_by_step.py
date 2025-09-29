#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步调试照片导入过程
"""

import os
import sys
import tempfile
import shutil
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database_manager import DatabaseManager
from photo_importer import extract_exif_data, calculate_file_md5, extract_photo_datetime

def debug_import_step_by_step(test_photo_path=None):
    """逐步调试导入过程"""
    
    # 1. 准备测试环境
    print("1️⃣ 准备测试环境...")
    temp_dir = tempfile.mkdtemp(prefix="photo_test_")
    temp_db_path = os.path.join(temp_dir, "test.db")
    
    # 使用示例照片或用户指定的照片
    if test_photo_path:
        test_photo = test_photo_path
    else:
        # 尝试一些常见的照片路径
        possible_paths = [
            r"C:\Users\Public\Pictures\Sample Pictures",
            r"C:\Windows\Web\Wallpaper",
            r"D:\dele-1\mypm\test_photo.jpg"
        ]
        
        test_photo = None
        for base_path in possible_paths:
            if os.path.exists(base_path):
                if os.path.isdir(base_path):
                    # 查找第一个图片文件
                    for file in os.listdir(base_path):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            test_photo = os.path.join(base_path, file)
                            break
                else:
                    test_photo = base_path
                
                if test_photo and os.path.exists(test_photo):
                    break
        
        if not test_photo:
            print("❌ 找不到测试照片，请提供照片路径作为参数")
            print("用法: python debug_import_step_by_step.py [照片路径]")
            return False
    
    if not os.path.exists(test_photo):
        print(f"❌ 测试照片不存在: {test_photo}")
        return False
    
    print(f"✅ 临时目录: {temp_dir}")
    print(f"✅ 临时数据库: {temp_db_path}")
    print(f"✅ 测试照片: {test_photo}")
    
    try:
        # 2. 初始化数据库
        print("\n2️⃣ 初始化数据库...")
        db_manager = DatabaseManager(temp_db_path)
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return False
        
        if not db_manager.initialize():
            print("❌ 数据库初始化失败")
            return False
        
        print("✅ 数据库初始化成功")
        
        # 3. 提取文件信息
        print("\n3️⃣ 提取文件信息...")
        
        # 3.1 计算MD5和文件大小
        md5_hash, file_size = calculate_file_md5(test_photo)
        print(f"✅ MD5: {md5_hash}")
        print(f"✅ 文件大小: {file_size} 字节")
        
        # 3.2 提取照片时间
        photo_time = extract_photo_datetime(test_photo)
        print(f"✅ 照片时间: {photo_time}")
        
        # 3.3 提取EXIF数据
        exif_data = extract_exif_data(test_photo)
        print(f"✅ EXIF数据提取: {'成功' if exif_data else '失败'}")
        if exif_data:
            print(f"   EXIF字段数: {len(exif_data)}")
            if 'GPSInfo' in exif_data:
                gps_info = exif_data['GPSInfo']
                print(f"   GPS字段数: {len(gps_info)}")
                print(f"   GPS字段: {list(gps_info.keys())}")
            else:
                print("   ❌ 没有GPS信息")
        
        # 4. 准备数据库参数
        print("\n4️⃣ 准备数据库参数...")
        filename = os.path.basename(test_photo)
        relative_path = f"test/{filename}"
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        print(f"✅ 文件名: {filename}")
        print(f"✅ 相对路径: {relative_path}")
        print(f"✅ 文件扩展名: {file_ext}")
        print(f"✅ 创建时间: {photo_time.isoformat()}")
        
        # 5. 调用 add_photo_record
        print("\n5️⃣ 调用 add_photo_record...")
        print("参数:")
        print(f"  filename: {filename}")
        print(f"  relative_path: {relative_path}")
        print(f"  md5: {md5_hash}")
        print(f"  size: {file_size}")
        print(f"  created_at: {photo_time.isoformat()}")
        print(f"  photo_type: {file_ext}")
        print(f"  exif_data: {'有数据' if exif_data else '无数据'}")
        
        photo_id = db_manager.add_photo_record(
            filename=filename,
            relative_path=relative_path,
            md5=md5_hash,
            size=file_size,
            created_at=photo_time.isoformat(),
            photo_type=file_ext,
            exif_data=exif_data
        )
        
        if photo_id:
            print(f"✅ 照片记录添加成功，ID: {photo_id}")
        else:
            print("❌ 照片记录添加失败")
            return False
        
        # 6. 验证数据库记录
        print("\n6️⃣ 验证数据库记录...")
        photos = db_manager.get_all_photos()
        
        if not photos:
            print("❌ 数据库中没有照片记录")
            return False
        
        photo_record = photos[0]
        print(f"✅ 找到照片记录: {photo_record['filename']}")
        print(f"   照片ID: {photo_record['id']}")
        print(f"   文件大小: {photo_record['size']} 字节")
        print(f"   MD5: {photo_record['md5']}")
        print(f"   创建时间: {photo_record['created_at']}")
        print(f"   导入时间: {photo_record.get('imported_at', 'N/A')}")
        
        # 7. 检查原始 exif_json 字段
        print("\n7️⃣ 检查原始 exif_json 字段...")
        
        # 直接查询数据库获取原始数据
        db_manager.database.cursor.execute("SELECT exif_json FROM photos WHERE id = ?", (photo_id,))
        raw_result = db_manager.database.cursor.fetchone()
        
        if raw_result and raw_result[0]:
            exif_json_raw = raw_result[0]
            print(f"✅ 原始 exif_json 字段存在，长度: {len(exif_json_raw)} 字符")
            print(f"   前100字符: {exif_json_raw[:100]}...")
            
            try:
                parsed_exif = json.loads(exif_json_raw)
                print(f"✅ JSON解析成功，包含 {len(parsed_exif)} 个字段")
                
                if 'GPSInfo' in parsed_exif:
                    gps_info = parsed_exif['GPSInfo']
                    print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
                    print(f"   GPS字段: {list(gps_info.keys())}")
                else:
                    print("❌ 解析后的EXIF中没有GPS信息")
                    
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
        else:
            print("❌ 原始 exif_json 字段为空或不存在")
        
        # 8. 检查 get_all_photos 返回的 exif_data
        print("\n8️⃣ 检查 get_all_photos 返回的 exif_data...")
        exif_data_from_db = photo_record.get('exif_data', {})
        
        if exif_data_from_db:
            print(f"✅ exif_data 字段存在，包含 {len(exif_data_from_db)} 个字段")
            
            if 'GPSInfo' in exif_data_from_db:
                gps_info = exif_data_from_db['GPSInfo']
                print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
                print(f"   GPS字段: {list(gps_info.keys())}")
            else:
                print("❌ exif_data 中没有GPS信息")
        else:
            print("❌ exif_data 字段为空或不存在")
        
        print("\n✅ 调试完成")
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        try:
            if 'db_manager' in locals():
                db_manager.database.close()
            shutil.rmtree(temp_dir)
            print(f"✅ 清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️  清理临时目录失败: {e}")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    test_photo_path = None
    if len(sys.argv) > 1:
        test_photo_path = sys.argv[1]
    
    debug_import_step_by_step(test_photo_path)