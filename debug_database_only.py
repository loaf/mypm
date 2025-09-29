#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅测试数据库EXIF数据存储，不依赖实际照片文件
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

def create_mock_exif_data():
    """创建模拟的EXIF数据，包含GPS信息"""
    return {
        'Make': 'Canon',
        'Model': 'EOS R5',
        'DateTime': '2024:12:01 14:30:22',
        'ExifImageWidth': 8192,
        'ExifImageHeight': 5464,
        'FNumber': 2.8,
        'ExposureTime': '1/125',
        'ISOSpeedRatings': 100,
        'FocalLength': 85.0,
        'GPSInfo': {
            'GPSVersionID': (2, 3, 0, 0),
            'GPSLatitudeRef': 'N',
            'GPSLatitude': ((39, 1), (54, 1), (2643, 100)),
            'GPSLongitudeRef': 'E',
            'GPSLongitude': ((116, 1), (23, 1), (5123, 100)),
            'GPSAltitudeRef': 0,
            'GPSAltitude': (45, 1),
            'GPSTimeStamp': ((6, 1), (30, 1), (22, 1)),
            'GPSDateStamp': '2024:12:01'
        }
    }

def debug_database_exif_storage():
    """测试数据库EXIF数据存储"""
    
    # 1. 准备测试环境
    print("1️⃣ 准备测试环境...")
    temp_dir = tempfile.mkdtemp(prefix="photo_test_")
    temp_db_path = os.path.join(temp_dir, "test.db")
    
    print(f"✅ 临时目录: {temp_dir}")
    print(f"✅ 临时数据库: {temp_db_path}")
    
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
        
        # 3. 创建模拟数据
        print("\n3️⃣ 创建模拟数据...")
        exif_data = create_mock_exif_data()
        
        print(f"✅ 模拟EXIF数据创建成功，包含 {len(exif_data)} 个字段")
        if 'GPSInfo' in exif_data:
            gps_info = exif_data['GPSInfo']
            print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
            print(f"   GPS字段: {list(gps_info.keys())}")
        
        # 4. 准备数据库参数
        print("\n4️⃣ 准备数据库参数...")
        filename = "test_photo.jpg"
        relative_path = "test/test_photo.jpg"
        md5_hash = "abcd1234567890abcd1234567890abcd"
        file_size = 1024000
        created_at = datetime.now().isoformat()
        photo_type = "jpg"
        
        print(f"✅ 文件名: {filename}")
        print(f"✅ 相对路径: {relative_path}")
        print(f"✅ MD5: {md5_hash}")
        print(f"✅ 文件大小: {file_size}")
        print(f"✅ 创建时间: {created_at}")
        print(f"✅ 照片类型: {photo_type}")
        
        # 5. 调用 add_photo_record
        print("\n5️⃣ 调用 add_photo_record...")
        print("参数:")
        print(f"  filename: {filename}")
        print(f"  relative_path: {relative_path}")
        print(f"  md5: {md5_hash}")
        print(f"  size: {file_size}")
        print(f"  created_at: {created_at}")
        print(f"  photo_type: {photo_type}")
        print(f"  exif_data: 有数据 ({len(exif_data)} 个字段)")
        
        photo_id = db_manager.add_photo_record(
            filename=filename,
            relative_path=relative_path,
            md5=md5_hash,
            size=file_size,
            created_at=created_at,
            photo_type=photo_type,
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
            print(f"   前200字符: {exif_json_raw[:200]}...")
            
            try:
                parsed_exif = json.loads(exif_json_raw)
                print(f"✅ JSON解析成功，包含 {len(parsed_exif)} 个字段")
                
                if 'GPSInfo' in parsed_exif:
                    gps_info = parsed_exif['GPSInfo']
                    print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
                    print(f"   GPS字段: {list(gps_info.keys())}")
                    
                    # 检查具体的GPS数据
                    if 'GPSLatitude' in gps_info:
                        print(f"   GPS纬度: {gps_info['GPSLatitude']}")
                    if 'GPSLongitude' in gps_info:
                        print(f"   GPS经度: {gps_info['GPSLongitude']}")
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
                
                # 检查具体的GPS数据
                if 'GPSLatitude' in gps_info:
                    print(f"   GPS纬度: {gps_info['GPSLatitude']}")
                if 'GPSLongitude' in gps_info:
                    print(f"   GPS经度: {gps_info['GPSLongitude']}")
            else:
                print("❌ exif_data 中没有GPS信息")
        else:
            print("❌ exif_data 字段为空或不存在")
        
        # 9. 测试数据一致性
        print("\n9️⃣ 测试数据一致性...")
        if raw_result and raw_result[0] and exif_data_from_db:
            original_gps = exif_data.get('GPSInfo', {})
            stored_gps = exif_data_from_db.get('GPSInfo', {})
            
            if original_gps and stored_gps:
                print("✅ 原始GPS数据和存储GPS数据都存在")
                
                # 比较关键字段
                for key in ['GPSLatitude', 'GPSLongitude', 'GPSLatitudeRef', 'GPSLongitudeRef']:
                    if key in original_gps and key in stored_gps:
                        if original_gps[key] == stored_gps[key]:
                            print(f"   ✅ {key}: 数据一致")
                        else:
                            print(f"   ❌ {key}: 数据不一致")
                            print(f"      原始: {original_gps[key]}")
                            print(f"      存储: {stored_gps[key]}")
                    else:
                        print(f"   ⚠️  {key}: 字段缺失")
            else:
                print("❌ GPS数据缺失")
        
        print("\n✅ 数据库EXIF存储测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
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
    debug_database_exif_storage()