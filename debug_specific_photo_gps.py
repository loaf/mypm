#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证特定照片的GPS数据完整性
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from db.database_manager import DatabaseManager

def check_specific_photo_gps(photo_filename="IMG_20250819_094620.jpg"):
    """检查特定照片的GPS数据"""
    print(f"🔍 检查照片 {photo_filename} 的GPS数据")
    print("=" * 60)
    
    try:
        # 初始化数据库管理器
        db_path = os.path.join(project_root, "myphotolib/.library.db")
        db_manager = DatabaseManager(db_path)
        
        # 1. 直接查询数据库获取照片信息
        print("1️⃣ 直接查询数据库...")
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        
        # 查询包含指定文件名的照片
        cursor.execute("""
            SELECT id, filename, path, exif_json, size, md5
            FROM photos
            WHERE filename LIKE ?
        """, (f"%{photo_filename}%",))
        
        photos = cursor.fetchall()
        
        if not photos:
            print(f"❌ 未找到包含 '{photo_filename}' 的照片记录")
            return False
            
        print(f"✅ 找到 {len(photos)} 条匹配记录")
        
        for i, photo in enumerate(photos, 1):
            photo_id, filename, path, exif_json, file_size, md5_hash = photo
            print(f"\n📸 记录 {i}:")
            print(f"   ID: {photo_id}")
            print(f"   文件名: {filename}")
            print(f"   路径: {path}")
            print(f"   文件大小: {file_size} bytes")
            print(f"   MD5: {md5_hash}")
            
            # 2. 检查exif_json字段
            print(f"\n2️⃣ 检查EXIF数据...")
            if exif_json:
                try:
                    exif_data = json.loads(exif_json)
                    print(f"✅ EXIF数据解析成功，包含 {len(exif_data)} 个字段")
                    
                    # 查找GPS相关字段
                    gps_fields = {k: v for k, v in exif_data.items() if 'GPS' in k}
                    if gps_fields:
                        print(f"🌍 找到 {len(gps_fields)} 个GPS字段:")
                        for gps_key, gps_value in gps_fields.items():
                            print(f"   {gps_key}: {gps_value}")
                            
                        # 3. 检查关键GPS字段
                        print(f"\n3️⃣ 检查关键GPS字段...")
                        required_gps_fields = ['GPSLatitude', 'GPSLongitude', 'GPSLatitudeRef', 'GPSLongitudeRef']
                        missing_fields = []
                        
                        for field in required_gps_fields:
                            if field in gps_fields:
                                print(f"   ✅ {field}: {gps_fields[field]}")
                            else:
                                missing_fields.append(field)
                                print(f"   ❌ {field}: 缺失")
                        
                        if not missing_fields:
                            print("✅ 所有关键GPS字段都存在")
                            
                            # 4. 尝试解析GPS坐标
                            print(f"\n4️⃣ 解析GPS坐标...")
                            try:
                                lat_data = gps_fields.get('GPSLatitude')
                                lon_data = gps_fields.get('GPSLongitude')
                                lat_ref = gps_fields.get('GPSLatitudeRef')
                                lon_ref = gps_fields.get('GPSLongitudeRef')
                                
                                if lat_data and lon_data and lat_ref and lon_ref:
                                    # 转换为十进制度数
                                    def dms_to_decimal(dms_data):
                                        if isinstance(dms_data, list) and len(dms_data) == 3:
                                            degrees = dms_data[0][0] / dms_data[0][1] if isinstance(dms_data[0], list) else dms_data[0]
                                            minutes = dms_data[1][0] / dms_data[1][1] if isinstance(dms_data[1], list) else dms_data[1]
                                            seconds = dms_data[2][0] / dms_data[2][1] if isinstance(dms_data[2], list) else dms_data[2]
                                            return degrees + minutes/60 + seconds/3600
                                        return None
                                    
                                    lat_decimal = dms_to_decimal(lat_data)
                                    lon_decimal = dms_to_decimal(lon_data)
                                    
                                    if lat_decimal is not None and lon_decimal is not None:
                                        # 应用方向参考
                                        if lat_ref == 'S':
                                            lat_decimal = -lat_decimal
                                        if lon_ref == 'W':
                                            lon_decimal = -lon_decimal
                                            
                                        print(f"   📍 纬度: {lat_decimal:.6f}° ({lat_ref})")
                                        print(f"   📍 经度: {lon_decimal:.6f}° ({lon_ref})")
                                        print(f"   🗺️ 坐标: ({lat_decimal:.6f}, {lon_decimal:.6f})")
                                        
                                        # 生成地图链接
                                        baidu_url = f"https://map.baidu.com/?q={lat_decimal},{lon_decimal}"
                                        print(f"   🔗 百度地图: {baidu_url}")
                                        
                                    else:
                                        print("   ❌ GPS坐标解析失败")
                                else:
                                    print("   ❌ GPS坐标数据不完整")
                                    
                            except Exception as e:
                                print(f"   ❌ GPS坐标解析出错: {e}")
                        else:
                            print(f"❌ 缺失关键GPS字段: {missing_fields}")
                    else:
                        print("❌ 未找到GPS信息")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ EXIF数据解析失败: {e}")
            else:
                print("❌ 无EXIF数据")
        
        # 5. 使用DatabaseManager的get_all_photos方法测试
        print(f"\n5️⃣ 使用DatabaseManager.get_all_photos()测试...")
        all_photos = db_manager.get_all_photos()
        matching_photos = [p for p in all_photos if photo_filename in p.get('filename', '')]
        
        if matching_photos:
            print(f"✅ get_all_photos()找到 {len(matching_photos)} 条匹配记录")
            for photo in matching_photos:
                print(f"   文件名: {photo.get('filename')}")
                exif_data = photo.get('exif_data')
                if exif_data:
                    gps_fields = {k: v for k, v in exif_data.items() if 'GPS' in k}
                    if gps_fields:
                        print(f"   🌍 GPS字段数量: {len(gps_fields)}")
                        print(f"   📍 包含GPS坐标: {'GPSLatitude' in gps_fields and 'GPSLongitude' in gps_fields}")
                    else:
                        print("   ❌ 无GPS数据")
                else:
                    print("   ❌ 无exif_data字段")
        else:
            print(f"❌ get_all_photos()未找到匹配记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 检查命令行参数
    photo_name = "IMG_20250819_094620.jpg"
    if len(sys.argv) > 1:
        photo_name = sys.argv[1]
    
    print(f"🔍 GPS数据完整性检查")
    print(f"目标照片: {photo_name}")
    print("=" * 60)
    
    success = check_specific_photo_gps(photo_name)
    
    if success:
        print("\n✅ 检查完成")
    else:
        print("\n❌ 检查失败")