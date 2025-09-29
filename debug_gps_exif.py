#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：读取指定照片的EXIF数据，特别是GPS信息
"""

import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def debug_exif_gps(image_path):
    """调试读取照片的EXIF和GPS信息"""
    print(f"=== 调试照片EXIF信息 ===")
    print(f"文件路径: {image_path}")
    print(f"文件存在: {os.path.exists(image_path)}")
    
    if not os.path.exists(image_path):
        print("❌ 文件不存在")
        return
    
    try:
        # 打开图片
        with Image.open(image_path) as img:
            print(f"图片格式: {img.format}")
            print(f"图片尺寸: {img.size}")
            print(f"图片模式: {img.mode}")
            
            # 获取EXIF数据
            exif_data = img._getexif()
            
            if exif_data is None:
                print("❌ 该图片没有EXIF数据")
                return
            
            print(f"\n=== 原始EXIF数据 ===")
            print(f"EXIF条目数量: {len(exif_data)}")
            
            # 解析所有EXIF标签
            parsed_exif = {}
            gps_info = None
            
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                parsed_exif[tag_name] = value
                
                # 特别处理GPS信息
                if tag_name == 'GPSInfo':
                    gps_info = value
                    print(f"\n🎯 发现GPS信息!")
                    print(f"GPS原始数据: {value}")
                    
                    # 解析GPS标签
                    gps_parsed = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_parsed[gps_tag_name] = gps_value
                        print(f"  {gps_tag_name}: {gps_value}")
                    
                    # 尝试计算经纬度
                    if 'GPSLatitude' in gps_parsed and 'GPSLongitude' in gps_parsed:
                        lat_dms = gps_parsed['GPSLatitude']
                        lon_dms = gps_parsed['GPSLongitude']
                        lat_ref = gps_parsed.get('GPSLatitudeRef', 'N')
                        lon_ref = gps_parsed.get('GPSLongitudeRef', 'E')
                        
                        print(f"\n📍 GPS坐标解析:")
                        print(f"  纬度DMS: {lat_dms} {lat_ref}")
                        print(f"  经度DMS: {lon_dms} {lon_ref}")
                        
                        # 转换为十进制度
                        def dms_to_decimal(dms):
                            degrees = float(dms[0])
                            minutes = float(dms[1])
                            seconds = float(dms[2])
                            return degrees + minutes/60.0 + seconds/3600.0
                        
                        lat_decimal = dms_to_decimal(lat_dms)
                        lon_decimal = dms_to_decimal(lon_dms)
                        
                        if lat_ref == 'S':
                            lat_decimal = -lat_decimal
                        if lon_ref == 'W':
                            lon_decimal = -lon_decimal
                            
                        print(f"  纬度十进制: {lat_decimal}")
                        print(f"  经度十进制: {lon_decimal}")
                        print(f"  Google Maps: https://maps.google.com/?q={lat_decimal},{lon_decimal}")
            
            # 显示关键EXIF信息
            print(f"\n=== 关键EXIF信息 ===")
            key_tags = ['DateTime', 'DateTimeOriginal', 'Make', 'Model', 'Software', 'GPSInfo']
            for tag in key_tags:
                if tag in parsed_exif:
                    print(f"{tag}: {parsed_exif[tag]}")
            
            if gps_info is None:
                print("❌ 未找到GPS信息")
            else:
                print("✅ GPS信息读取成功")
                
    except Exception as e:
        print(f"❌ 读取EXIF失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 指定要调试的照片路径
    photo_path = r"D:\dele-1\mypm\myphotolib\2025\08\19\IMG_20250819_181023.jpg"
    debug_exif_gps(photo_path)