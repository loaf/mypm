# MyPhotoApp - 个人照片管理软件

基于 Python + PyQt5 的跨平台桌面照片管理应用程序。

## 功能特性

- 📁 照片库管理：创建和管理独立的照片库
- 📷 照片导入：支持多种图片和视频格式
- 🗂️ 智能组织：按日期自动组织照片
- 🔍 重复检测：基于MD5避免重复导入
- 📊 详细信息：显示EXIF信息和文件详情
- 🎯 跨平台：支持Windows、macOS、Linux

## 系统要求

- Python 3.7+
- PyQt6
- 支持的操作系统：Windows 10+, macOS 10.14+, Ubuntu 18.04+

## 安装和运行

### 1. 克隆项目
```bash
git clone <repository-url>
cd mypm
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行程序
```bash
python main.py
```

## M1 阶段功能

当前版本（M1）实现了以下基础功能：

- ✅ 项目结构搭建
- ✅ 配置管理（config.json）
- ✅ 照片库目录管理
- ✅ SQLite数据库初始化
- ✅ 基础PyQt界面
- ✅ 照片库创建/打开/切换

### 使用说明

1. **首次运行**：程序会在当前目录下创建默认照片库 `myphotolib`
2. **新建照片库**：菜单 → 照片库 → 新建照片库
3. **打开照片库**：菜单 → 照片库 → 打开照片库
4. **查看信息**：菜单 → 照片库 → 照片库信息

## 项目结构

```
mypm/
├── main.py              # 程序入口
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明
├── ui/                 # PyQt界面模块
│   ├── __init__.py
│   └── main_window.py  # 主窗口
├── core/               # 核心业务逻辑
│   ├── __init__.py
│   ├── config_manager.py    # 配置管理
│   └── photo_library.py     # 照片库管理
├── db/                 # 数据库操作
│   ├── __init__.py
│   └── database.py     # SQLite数据库操作
├── libs/               # 第三方工具封装
│   └── __init__.py
└── resources/          # 资源文件
    └── __init__.py
```

## 数据库结构

### photos 表
- id: 主键
- filename: 文件名
- path: 文件路径
- md5: MD5哈希值
- size: 文件大小
- created_at: 创建时间
- imported_at: 导入时间
- type: 文件类型
- exif_json: EXIF信息（JSON格式）
- thumbnail_path: 缩略图路径
- is_deleted: 是否已删除

### config 表
- key: 配置键
- value: 配置值
- updated_at: 更新时间

## 配置文件

程序会在运行目录生成 `config.json` 配置文件，包含：

- 应用设置
- 照片库路径
- 界面设置
- 导入设置

## 开发计划

- **M1 阶段** ✅：项目初始化 + 照片库管理
- **M2 阶段**：照片导入 + EXIF解析
- **M3 阶段**：缩略图生成 + 照片浏览
- **M4 阶段**：搜索 + 排序 + 过滤
- **M5 阶段**：标签 + 相册功能
- **M6 阶段**：性能优化 + 打包发布

## 故障排除

### 常见问题

1. **PyQt5 安装失败**
   ```bash
   pip install PyQt5 -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

2. **数据库权限错误**
   - 确保照片库目录有写入权限
   - 检查磁盘空间是否充足

3. **程序无法启动**
   - 检查Python版本（需要3.7+）
   - 确认所有依赖包已正确安装

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**注意**：这是M1阶段的基础版本，后续功能正在开发中。