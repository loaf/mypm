#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试导入过程中的EXIF数据提取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from photo_importer import extract_exif_data

def test_exif_extraction():
    """测试EXIF数据提取"""
    test_photo = r"D:\dele-1\mypm\myphotolib\2025\08\19\IMG_20250819_181023.jpg"
    
    print("=== 测试导入过程中的EXIF数据提取 ===")
    print(f"测试照片: {test_photo}")
    
    # 检查文件是否存在
    if not os.path.exists(test_photo):
        print("❌ 测试照片不存在")
        return
    
    print("✅ 照片文件存在")
    
    # 调用extract_exif_data函数
    print("\n📋 调用 extract_exif_data 函数...")
    try:
        exif_data = extract_exif_data(test_photo)
        
        if exif_data is None:
            print("❌ extract_exif_data 返回 None")
            return
        
        if not exif_data:
            print("❌ extract_exif_data 返回空字典")
            return
        
        print(f"✅ 成功提取EXIF数据，包含 {len(exif_data)} 个字段")
        
        # 检查GPS信息
        if 'GPSInfo' in exif_data:
            gps_info = exif_data['GPSInfo']
            print(f"✅ 包含GPS信息，{len(gps_info)} 个GPS字段")
            print(f"   GPS字段: {list(gps_info.keys())}")
            
            # 检查关键字段
            required_fields = ['GPSLatitude', 'GPSLongitude', 'GPSLatitudeRef', 'GPSLongitudeRef']
            for field in required_fields:
                if field in gps_info:
                    print(f"   ✅ {field}: {gps_info[field]}")
                else:
                    print(f"   ❌ 缺少 {field}")
        else:
            print("❌ 未找到GPS信息")
        
        # 显示其他重要EXIF字段
        important_fields = ['Make', 'Model', 'DateTime', 'DateTimeOriginal']
        print(f"\n📋 其他重要EXIF字段:")
        for field in important_fields:
            if field in exif_data:
                print(f"   ✅ {field}: {exif_data[field]}")
            else:
                print(f"   ❌ 缺少 {field}")
        
        # 测试JSON序列化
        print(f"\n🔄 测试JSON序列化...")
        import json
        try:
            json_str = json.dumps(exif_data, ensure_ascii=False)
            print(f"✅ JSON序列化成功，长度: {len(json_str)} 字符")
            
            # 测试反序列化
            parsed_data = json.loads(json_str)
            print(f"✅ JSON反序列化成功，包含 {len(parsed_data)} 个字段")
            
            if 'GPSInfo' in parsed_data:
                print(f"✅ GPS信息在序列化后保持完整")
            else:
                print(f"❌ GPS信息在序列化后丢失")
                
        except Exception as e:
            print(f"❌ JSON序列化失败: {e}")
        
    except Exception as e:
        print(f"❌ extract_exif_data 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exif_extraction()