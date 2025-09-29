#!/usr/bin/env python3
"""
调试脚本：分析GPS EXIF数据结构
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json

def analyze_gps_structure(file_path):
    """分析GPS EXIF数据的具体结构"""
    print(f"分析照片: {file_path}")
    
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            
            if exif_data is None:
                print("❌ 无EXIF数据")
                return
                
            print("✅ 找到EXIF数据")
            
            # 查找GPS相关的标签
            gps_tags = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # 打印所有标签的类型和值
                print(f"标签 {tag} (ID: {tag_id}): 类型={type(value)}, 值={repr(value)}")
                
                if tag == 'GPSInfo':
                    gps_tags[tag] = value
                    print(f"🎯 找到GPS信息: {type(value)}")
                    
                    # 如果是字典，解析GPS子标签
                    if isinstance(value, dict):
                        print("GPS子标签:")
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            print(f"  {gps_tag} (ID: {gps_tag_id}): 类型={type(gps_value)}, 值={repr(gps_value)}")
            
            if not gps_tags:
                print("❌ 未找到GPS信息标签")
            else:
                print(f"✅ GPS标签数量: {len(gps_tags)}")
                
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    photo_path = r"D:\dele-1\mypm\myphotolib\2025\08\19\IMG_20250819_181023.jpg"
    analyze_gps_structure(photo_path)