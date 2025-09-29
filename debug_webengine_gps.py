#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebEngine和GPS地图显示诊断脚本
检查WebEngine安装状态和GPS数据传递逻辑
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_webengine_availability():
    """测试WebEngine的可用性"""
    print("🔍 WebEngine可用性测试")
    print("=" * 50)
    
    # 1. 测试PyQt6.QtWebEngineWidgets导入
    print("\n1️⃣ 测试PyQt6.QtWebEngineWidgets导入...")
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        print("✅ PyQt6.QtWebEngineWidgets.QWebEngineView 导入成功")
        webengine_available = True
    except ImportError as e:
        print(f"❌ PyQt6.QtWebEngineWidgets 导入失败: {e}")
        webengine_available = False
    except Exception as e:
        print(f"❌ PyQt6.QtWebEngineWidgets 导入异常: {e}")
        webengine_available = False
    
    # 2. 测试主窗口中的WebEngine状态
    print("\n2️⃣ 测试主窗口中的WebEngine状态...")
    try:
        from ui.main_window import WEB_ENGINE_AVAILABLE
        print(f"✅ 主窗口中WEB_ENGINE_AVAILABLE = {WEB_ENGINE_AVAILABLE}")
        
        if WEB_ENGINE_AVAILABLE != webengine_available:
            print(f"⚠️  状态不一致: 直接导入={webengine_available}, 主窗口={WEB_ENGINE_AVAILABLE}")
    except Exception as e:
        print(f"❌ 无法获取主窗口WebEngine状态: {e}")
    
    # 3. 检查PyQt6版本和WebEngine支持
    print("\n3️⃣ 检查PyQt6版本和WebEngine支持...")
    try:
        import PyQt6
        print(f"✅ PyQt6版本: {PyQt6.QtCore.PYQT_VERSION_STR}")
        
        # 检查Qt版本
        print(f"✅ Qt版本: {PyQt6.QtCore.QT_VERSION_STR}")
        
        # 尝试列出可用的WebEngine模块
        try:
            import PyQt6.QtWebEngineWidgets
            print("✅ QtWebEngineWidgets模块可用")
        except ImportError:
            print("❌ QtWebEngineWidgets模块不可用")
            
        try:
            import PyQt6.QtWebEngineCore
            print("✅ QtWebEngineCore模块可用")
        except ImportError:
            print("❌ QtWebEngineCore模块不可用")
            
    except Exception as e:
        print(f"❌ PyQt6版本检查失败: {e}")
    
    return webengine_available

def test_gps_data_flow():
    """测试GPS数据流转过程"""
    print("\n\n🌍 GPS数据流转测试")
    print("=" * 50)
    
    # 1. 连接数据库获取GPS数据
    print("\n1️⃣ 从数据库获取GPS数据...")
    try:
        from db.database_manager import DatabaseManager
        from core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        photo_library_path = config_manager.get_photo_library_path()
        db_path = os.path.join(photo_library_path, '.library.db')
        
        print(f"📁 照片库路径: {photo_library_path}")
        print(f"🗄️ 数据库路径: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
            
        db_manager = DatabaseManager(db_path)
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return False
            
        # 查找包含GPS信息的照片
        photos = db_manager.get_all_photos()
        gps_photos = []
        
        for photo in photos:
            exif_data = photo.get('exif_data', {})
            if isinstance(exif_data, dict) and 'GPSInfo' in exif_data:
                gps_info = exif_data['GPSInfo']
                if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                    gps_photos.append(photo)
        
        print(f"✅ 找到 {len(gps_photos)} 张包含GPS信息的照片")
        
        if not gps_photos:
            print("❌ 没有找到包含GPS信息的照片")
            return False
            
        # 选择第一张GPS照片进行测试
        test_photo = gps_photos[0]
        print(f"📸 测试照片: {test_photo.get('filename')}")
        
    except Exception as e:
        print(f"❌ 数据库GPS数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. 测试GPS解析方法
    print("\n2️⃣ 测试GPS解析方法...")
    try:
        from ui.main_window import MainWindow
        
        # 创建MainWindow实例（不显示UI）
        import PyQt6.QtWidgets
        app = PyQt6.QtWidgets.QApplication.instance()
        if app is None:
            app = PyQt6.QtWidgets.QApplication([])
        
        main_window = MainWindow()
        
        # 测试parse_gps方法
        exif_data = test_photo.get('exif_data', {})
        gps_coords = main_window.parse_gps(exif_data)
        
        if gps_coords:
            lat, lon = gps_coords
            print(f"✅ GPS解析成功: 纬度={lat:.6f}, 经度={lon:.6f}")
        else:
            print("❌ GPS解析失败，返回None")
            return False
            
    except Exception as e:
        print(f"❌ GPS解析方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试地图更新逻辑
    print("\n3️⃣ 测试地图更新逻辑...")
    try:
        # 检查WebEngine状态
        from ui.main_window import WEB_ENGINE_AVAILABLE
        print(f"🔧 WebEngine可用状态: {WEB_ENGINE_AVAILABLE}")
        
        if WEB_ENGINE_AVAILABLE:
            print("✅ WebEngine可用，应该显示地图")
            
            # 模拟update_map调用
            print(f"🗺️ 模拟地图更新: update_map({lat:.6f}, {lon:.6f})")
            
            # 检查地图HTML生成
            html_template = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <title>照片位置</title>
  <style>
    body {{ margin: 0; padding: 0; }}
    #map {{ height: 100vh; width: 100%; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    // 使用百度地图API显示位置
    var map = new BMap.Map("map");
    var point = new BMap.Point({lon:.6f}, {lat:.6f});
    map.centerAndZoom(point, 15);
    var marker = new BMap.Marker(point);
    map.addOverlay(marker);
    map.addControl(new BMap.NavigationControl());
  </script>
  <script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=YOUR_API_KEY"></script>
</body>
</html>"""
            
            print("✅ 地图HTML模板生成成功")
            
        else:
            print("❌ WebEngine不可用，将显示占位符")
            print("📝 占位符文本: '未检测到GPS信息或未安装WebEngine'")
            
    except Exception as e:
        print(f"❌ 地图更新逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_map_display_conditions():
    """测试地图显示的各种条件"""
    print("\n\n🎯 地图显示条件测试")
    print("=" * 50)
    
    # 1. WebEngine可用性
    print("\n1️⃣ WebEngine可用性检查...")
    webengine_ok = test_webengine_availability()
    
    # 2. GPS数据可用性
    print("\n2️⃣ GPS数据可用性检查...")
    gps_ok = test_gps_data_flow()
    
    # 3. 综合判断
    print("\n3️⃣ 综合判断...")
    if webengine_ok and gps_ok:
        print("✅ 所有条件满足，地图应该正常显示")
        print("🎯 建议检查: 地图API密钥、网络连接、HTML模板")
    elif not webengine_ok and gps_ok:
        print("⚠️  GPS数据正常，但WebEngine不可用")
        print("💡 建议: 安装PyQt6-WebEngine包")
        print("   命令: pip install PyQt6-WebEngine")
    elif webengine_ok and not gps_ok:
        print("⚠️  WebEngine可用，但GPS数据有问题")
        print("💡 建议: 检查数据库中的GPS数据完整性")
    else:
        print("❌ WebEngine和GPS数据都有问题")
        print("💡 建议: 先安装WebEngine，再检查GPS数据")
    
    return webengine_ok, gps_ok

if __name__ == "__main__":
    print("🚀 WebEngine和GPS地图显示诊断")
    print("=" * 60)
    
    try:
        webengine_ok, gps_ok = test_map_display_conditions()
        
        print(f"\n📊 诊断结果:")
        print(f"   WebEngine可用: {'✅' if webengine_ok else '❌'}")
        print(f"   GPS数据正常: {'✅' if gps_ok else '❌'}")
        
        if webengine_ok and gps_ok:
            print(f"\n🎉 诊断完成，地图功能应该正常工作")
        else:
            print(f"\n🔧 诊断完成，发现问题需要修复")
            
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()