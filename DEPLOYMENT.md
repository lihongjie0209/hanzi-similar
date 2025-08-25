# 生产环境部署说明

本项目提供了多种部署方式：脚本部署和Docker部署。

## 方式一：脚本部署

### 脚本文件

- `start-prod.sh` - Linux/macOS 版本
- `start-prod.bat` - Windows 版本

### 功能特性

✅ **自动创建Python虚拟环境** (使用 `python -m venv`)  
✅ **自动安装生产依赖** (只安装 `[prod]` 组依赖)  
✅ **使用Gunicorn + Uvicorn Workers** (生产级ASGI服务器)  
✅ **多进程部署** (默认4个worker进程)  
✅ **健康检查** (检查必要文件和目录)  
✅ **环境变量配置** (支持自定义主机、端口等)  

### 使用方法

#### Linux/macOS

```bash
# 添加执行权限
chmod +x start-prod.sh

# 启动服务
./start-prod.sh
```

#### Windows

```cmd
# 直接运行
start-prod.bat

# 或者双击执行
```

## 方式二：Docker部署

### 从Docker Hub运行

最简单的方式是直接从Docker Hub拉取并运行：

```bash
# 拉取并运行最新版本
docker run -p 8000:8000 lihongjie0209/hanzi-similar:latest

# 或者指定版本
docker run -p 8000:8000 lihongjie0209/hanzi-similar:v0.1.0

# 后台运行
docker run -d -p 8000:8000 --name hanzi-similar lihongjie0209/hanzi-similar:latest
```

### 使用docker-compose

```bash
# 使用项目提供的docker-compose.yml
docker-compose up -d

# 或者直接使用Docker Hub镜像
version: '3.8'
services:
  hanzi-similar:
    image: lihongjie0209/hanzi-similar:latest
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### 本地构建

如果需要自定义构建：

```bash
# 构建镜像
docker build -t hanzi-similar:latest .

# 运行容器
docker run -p 8000:8000 hanzi-similar:latest
```

## 环境变量配置

可以通过环境变量自定义配置：

```bash
# Linux/macOS
export HOST=0.0.0.0
export PORT=8080
export WORKERS=8
./start-prod.sh

# Windows (CMD)
set HOST=0.0.0.0
set PORT=8080
set WORKERS=8
start-prod.bat

# Windows (PowerShell)
$env:HOST="0.0.0.0"
$env:PORT="8080"
$env:WORKERS="8"
.\start-prod.bat
```

## 默认配置

- **主机**: `0.0.0.0` (监听所有网络接口)
- **端口**: `8000`
- **工作进程数**: `4`
- **超时时间**: `120秒`
- **最大请求数**: `1000` (之后重启worker)

## 生产依赖

脚本会自动安装以下生产环境必需的依赖：

- `chromadb` - 向量数据库
- `fastapi` - Web框架
- `fonttools` - 字体处理
- `gunicorn` - ASGI服务器
- `numpy` - 数值计算
- `uvicorn` - ASGI工作进程

## 注意事项

1. **向量数据库**: 确保运行前已经构建了 `chroma_db` 目录
2. **字体文件**: 确保 `fonts/` 目录存在且包含字体文件
3. **Python版本**: 需要 Python 3.13+
4. **防火墙**: 确保端口 8000 (或自定义端口) 已开放

## 访问API

服务启动后，可以通过以下URL访问：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/healthz
- **Web界面**: http://localhost:8000/ui/

## 日志

Gunicorn会将访问日志和错误日志输出到控制台，便于监控和调试。
