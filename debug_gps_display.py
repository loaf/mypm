#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GPS数据显示测试脚本
测试GPS坐标的解析、格式化和显示功能
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

def create_gps_test_data():
    """创建包含GPS信息的测试EXIF数据"""
    return {
        "Make": "Canon",
        "Model": "EOS R5", 
        "DateTime": "2024:12:01 14:30:22",
        "ExifImageWidth": 8192,
        "ExifImageHeight": 5464,
        "FNumber": 2.8,
        "ExposureTime": "1/125",
        "ISOSpeedRatings": 100,
        "FocalLength": 85.0,
        "GPSInfo": {
            "GPSVersionID": (2, 3, 0, 0),
            "GPSLatitudeRef": "N",  # 北纬
            "GPSLatitude": ((39, 1), (54, 1), (2643, 100)),  # 39°54'26.43"N (北京天安门)
            "GPSLongitudeRef": "E",  # 东经
            "GPSLongitude": ((116, 1), (23, 1), (5123, 100)),  # 116°23'51.23"E
            "GPSAltitudeRef": 0,  # 海平面以上
            "GPSAltitude": (4350, 100),  # 43.5米
            "GPSTimeStamp": ((6, 1), (30, 1), (22, 1)),  # 06:30:22 UTC
            "GPSDateStamp": "2024:12:01"
        }
    }

def dms_to_decimal(dms_tuple, ref):
    """
    将度分秒格式转换为十进制度数
    
    Args:
        dms_tuple: ((度, 1), (分, 1), (秒, 100)) 格式的元组
        ref: 参考方向 ('N', 'S', 'E', 'W')
    
    Returns:
        十进制度数
    """
    try:
        # 处理不同的数据格式
        if isinstance(dms_tuple, (list, tuple)) and len(dms_tuple) == 3:
            # 提取度、分、秒
            if isinstance(dms_tuple[0], (list, tuple)) and len(dms_tuple[0]) == 2:
                # 格式: [[度, 1], [分, 1], [秒, 100]]
                degrees = dms_tuple[0][0] / dms_tuple[0][1]
                minutes = dms_tuple[1][0] / dms_tuple[1][1] 
                seconds = dms_tuple[2][0] / dms_tuple[2][1]
            else:
                # 格式: (度, 分, 秒)
                degrees, minutes, seconds = dms_tuple
            
            # 转换为十进制
            decimal = degrees + minutes/60 + seconds/3600
            
            # 根据参考方向调整符号
            if ref in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        else:
            return None
    except (TypeError, IndexError, ZeroDivisionError):
        return None

def format_gps_coordinate(dms_tuple, ref):
    """
    格式化GPS坐标为可读字符串
    
    Args:
        dms_tuple: 度分秒元组
        ref: 参考方向
    
    Returns:
        格式化的坐标字符串
    """
    try:
        if isinstance(dms_tuple, (list, tuple)) and len(dms_tuple) == 3:
            if isinstance(dms_tuple[0], (list, tuple)) and len(dms_tuple[0]) == 2:
                # 格式: [[度, 1], [分, 1], [秒, 100]]
                degrees = dms_tuple[0][0] / dms_tuple[0][1]
                minutes = dms_tuple[1][0] / dms_tuple[1][1]
                seconds = dms_tuple[2][0] / dms_tuple[2][1]
            else:
                # 格式: (度, 分, 秒)
                degrees, minutes, seconds = dms_tuple
            
            return f"{degrees:.0f}°{minutes:.0f}'{seconds:.2f}\"{ref}"
        else:
            return "无效坐标"
    except (TypeError, IndexError, ZeroDivisionError):
        return "解析错误"

def format_altitude(altitude_tuple, ref):
    """
    格式化海拔高度
    
    Args:
        altitude_tuple: (高度值, 分母) 格式的元组
        ref: 参考值 (0=海平面以上, 1=海平面以下)
    
    Returns:
        格式化的海拔字符串
    """
    try:
        if isinstance(altitude_tuple, (list, tuple)) and len(altitude_tuple) == 2:
            altitude = altitude_tuple[0] / altitude_tuple[1]
            direction = "海平面以上" if ref == 0 else "海平面以下"
            return f"{altitude:.1f}米 ({direction})"
        else:
            return "无效海拔"
    except (TypeError, IndexError, ZeroDivisionError):
        return "解析错误"

def test_gps_data_display():
    """测试GPS数据的显示功能"""
    print("🌍 GPS数据显示测试")
    print("=" * 50)
    
    # 1. 创建临时环境
    print("\n1️⃣ 创建测试环境...")
    temp_dir = tempfile.mkdtemp(prefix="gps_test_")
    temp_db_path = os.path.join(temp_dir, "test.db")
    
    print(f"✅ 临时目录: {temp_dir}")
    print(f"✅ 临时数据库: {temp_db_path}")
    
    try:
        # 2. 初始化数据库并添加测试数据
        print("\n2️⃣ 初始化数据库...")
        db_manager = DatabaseManager(temp_db_path)
        if not db_manager.connect() or not db_manager.initialize():
            print("❌ 数据库初始化失败")
            return False
        
        # 3. 添加包含GPS数据的照片记录
        print("\n3️⃣ 添加GPS测试数据...")
        exif_data = create_gps_test_data()
        
        photo_id = db_manager.add_photo_record(
            filename="gps_test_photo.jpg",
            relative_path="test/gps_test_photo.jpg", 
            md5="gps123456789abcdef",
            size=2048000,
            created_at=datetime.now().isoformat(),
            photo_type="JPEG",
            exif_data=exif_data
        )
        
        if not photo_id:
            print("❌ 添加GPS测试数据失败")
            return False
        
        print(f"✅ GPS测试数据添加成功，照片ID: {photo_id}")
        
        # 4. 获取并解析GPS数据
        print("\n4️⃣ 获取并解析GPS数据...")
        photos = db_manager.get_all_photos()
        
        if not photos:
            print("❌ 未找到照片记录")
            return False
        
        photo = photos[0]
        exif_data = photo.get('exif_data', {})
        gps_info = exif_data.get('GPSInfo', {})
        
        if not gps_info:
            print("❌ 照片中没有GPS信息")
            return False
        
        print(f"✅ 找到GPS信息，包含 {len(gps_info)} 个GPS字段")
        
        # 5. 显示原始GPS数据
        print("\n5️⃣ 原始GPS数据:")
        for key, value in gps_info.items():
            print(f"   {key}: {value}")
        
        # 6. 解析和格式化GPS坐标
        print("\n6️⃣ GPS坐标解析:")
        
        # 纬度
        if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
            lat_dms = gps_info['GPSLatitude']
            lat_ref = gps_info['GPSLatitudeRef']
            lat_decimal = dms_to_decimal(lat_dms, lat_ref)
            lat_formatted = format_gps_coordinate(lat_dms, lat_ref)
            
            print(f"   纬度 (原始): {lat_dms}")
            print(f"   纬度 (格式化): {lat_formatted}")
            print(f"   纬度 (十进制): {lat_decimal:.6f}°")
        
        # 经度
        if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
            lon_dms = gps_info['GPSLongitude']
            lon_ref = gps_info['GPSLongitudeRef']
            lon_decimal = dms_to_decimal(lon_dms, lon_ref)
            lon_formatted = format_gps_coordinate(lon_dms, lon_ref)
            
            print(f"   经度 (原始): {lon_dms}")
            print(f"   经度 (格式化): {lon_formatted}")
            print(f"   经度 (十进制): {lon_decimal:.6f}°")
        
        # 海拔
        if 'GPSAltitude' in gps_info and 'GPSAltitudeRef' in gps_info:
            alt_tuple = gps_info['GPSAltitude']
            alt_ref = gps_info['GPSAltitudeRef']
            alt_formatted = format_altitude(alt_tuple, alt_ref)
            
            print(f"   海拔 (原始): {alt_tuple}, 参考: {alt_ref}")
            print(f"   海拔 (格式化): {alt_formatted}")
        
        # 时间信息
        if 'GPSTimeStamp' in gps_info:
            time_tuple = gps_info['GPSTimeStamp']
            if isinstance(time_tuple, (list, tuple)) and len(time_tuple) == 3:
                try:
                    if isinstance(time_tuple[0], (list, tuple)):
                        # 格式: [[时, 1], [分, 1], [秒, 1]]
                        hours = time_tuple[0][0] / time_tuple[0][1]
                        minutes = time_tuple[1][0] / time_tuple[1][1]
                        seconds = time_tuple[2][0] / time_tuple[2][1]
                    else:
                        # 格式: (时, 分, 秒)
                        hours, minutes, seconds = time_tuple
                    
                    print(f"   GPS时间 (原始): {time_tuple}")
                    print(f"   GPS时间 (格式化): {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f} UTC")
                except (TypeError, IndexError, ZeroDivisionError):
                    print(f"   GPS时间 (解析错误): {time_tuple}")
        
        if 'GPSDateStamp' in gps_info:
            date_stamp = gps_info['GPSDateStamp']
            print(f"   GPS日期: {date_stamp}")
        
        # 7. 生成地图链接
        print("\n7️⃣ 地图链接生成:")
        if lat_decimal is not None and lon_decimal is not None:
            # Google Maps链接
            google_maps_url = f"https://www.google.com/maps?q={lat_decimal},{lon_decimal}"
            print(f"   Google Maps: {google_maps_url}")
            
            # 百度地图链接 (需要坐标转换，这里仅作示例)
            baidu_maps_url = f"https://map.baidu.com/?q={lat_decimal},{lon_decimal}"
            print(f"   百度地图: {baidu_maps_url}")
        
        print("\n✅ GPS数据显示测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 8. 清理临时文件
        print("\n8️⃣ 清理临时文件...")
        try:
            if 'db_manager' in locals():
                db_manager.close()
            shutil.rmtree(temp_dir)
            print("✅ 临时文件清理完成")
        except Exception as e:
            print(f"⚠️  清理临时目录失败: {e}")

if __name__ == "__main__":
    test_gps_data_display()