#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试完整的照片导入过程
"""

import sys
import os
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from photo_importer import PhotoImporter
from db.database_manager import DatabaseManager

def test_full_import_process():
    """测试完整的照片导入过程"""
    test_photo = r"D:\dele-1\mypm\myphotolib\2025\08\19\IMG_20250819_181023.jpg"
    
    print("=== 完整照片导入过程测试 ===")
    print(f"测试照片: {test_photo}")
    
    # 创建临时目录和数据库
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test.db")
    
    print(f"📁 临时目录: {temp_dir}")
    print(f"📁 临时数据库: {temp_db}")
    
    try:
        # 1. 初始化导入器
        print("\n1️⃣ 初始化PhotoImporter...")
        importer = PhotoImporter(temp_dir, temp_db)
        
        # 2. 执行导入
        print("\n2️⃣ 执行照片导入...")
        result = importer.import_single_photo(test_photo)
        
        print(f"导入结果: {result}")
        
        if not result.get('success'):
            print(f"❌ 导入失败: {result.get('error', '未知错误')}")
            return
        
        print("✅ 照片导入成功")
        print(f"   目标路径: {result.get('target_path')}")
        
        # 3. 检查数据库记录
        print("\n3️⃣ 检查数据库记录...")
        db_manager = DatabaseManager(temp_db)
        
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return
        
        photos = db_manager.get_all_photos()
        if not photos:
            print("❌ 数据库中未找到照片记录")
            return
        
        photo_record = photos[0]
        print(f"✅ 找到照片记录: {photo_record['filename']}")
        print(f"   照片ID: {photo_record['id']}")
        print(f"   文件大小: {photo_record['size']} 字节")
        print(f"   MD5: {photo_record['md5']}")
        print(f"   创建时间: {photo_record['created_at']}")
        print(f"   导入时间: {photo_record.get('imported_at', 'N/A')}")
        
        # 4. 检查EXIF数据
        print("\n4️⃣ 检查EXIF数据...")
        exif_data = photo_record.get('exif_data', {})
        
        if not exif_data:
            print("❌ 照片记录中没有EXIF数据")
            
            # 检查原始JSON字段
            exif_json = photo_record.get('exif_json')
            if exif_json:
                print(f"⚠️  但是存在exif_json字段，长度: {len(exif_json)} 字符")
                try:
                    import json
                    parsed_exif = json.loads(exif_json)
                    print(f"✅ 成功解析exif_json，包含 {len(parsed_exif)} 个字段")
                    
                    if 'GPSInfo' in parsed_exif:
                        gps_info = parsed_exif['GPSInfo']
                        print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
                        print(f"   GPS字段: {list(gps_info.keys())}")
                    else:
                        print("❌ 解析后的EXIF中没有GPS信息")
                        
                except Exception as e:
                    print(f"❌ 解析exif_json失败: {e}")
            else:
                print("❌ 也没有exif_json字段")
            return
        
        print(f"✅ EXIF数据存在，包含 {len(exif_data)} 个字段")
        
        # 5. 检查GPS信息
        print("\n5️⃣ 检查GPS信息...")
        gps_info = exif_data.get('GPSInfo', {})
        
        if not gps_info:
            print("❌ EXIF数据中没有GPS信息")
            return
        
        print(f"✅ GPS信息存在，包含 {len(gps_info)} 个字段")
        print(f"   GPS字段: {list(gps_info.keys())}")
        
        # 检查关键GPS字段
        required_fields = ['GPSLatitude', 'GPSLongitude', 'GPSLatitudeRef', 'GPSLongitudeRef']
        for field in required_fields:
            if field in gps_info:
                print(f"   ✅ {field}: {gps_info[field]}")
            else:
                print(f"   ❌ 缺少 {field}")
        
        print("\n🎉 完整导入过程测试成功！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理临时文件
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 已清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️  清理临时目录失败: {e}")

if __name__ == "__main__":
    test_full_import_process()