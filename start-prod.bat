@echo off
REM 汉字相似度API生产环境启动脚本 (Windows版本)
REM 使用venv创建虚拟环境，安装prod依赖并启动服务器

setlocal enabledelayedexpansion

REM 脚本所在目录
cd /d "%~dp0"

REM 配置参数
set VENV_DIR=venv
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000
if "%WORKERS%"=="" set WORKERS=4

echo 🚀 汉字相似度API生产环境启动脚本
echo ================================

REM 检查Python版本
echo 📋 检查Python版本...
python --version
if errorlevel 1 (
    echo ❌ 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist "%VENV_DIR%" (
    echo 🔧 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ 错误: 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建完成
) else (
    echo 📦 虚拟环境已存在
)

REM 激活虚拟环境
echo 🔌 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"

REM 升级pip
echo ⬆️  升级pip...
python -m pip install --upgrade pip

REM 安装生产依赖
echo 📥 安装生产依赖...
pip install -e ".[prod]"
if errorlevel 1 (
    echo ❌ 错误: 依赖安装失败
    pause
    exit /b 1
)

REM 检查必要的目录和文件
echo 🔍 检查必要文件...
if not exist "api_main.py" (
    echo ❌ 错误: api_main.py 文件不存在
    pause
    exit /b 1
)

if not exist "chroma_db" (
    echo ⚠️  警告: chroma_db 目录不存在，请确保已经构建了向量数据库
)

if not exist "fonts" (
    echo ⚠️  警告: fonts 目录不存在，SVG渲染功能可能不可用
)

REM 显示启动信息
echo.
echo 🌟 准备启动服务器...
echo 主机: %HOST%
echo 端口: %PORT%
echo 工作进程数: %WORKERS%
echo.

REM 启动服务器
echo 🚀 启动Gunicorn服务器...
gunicorn api_main:app ^
    --workers %WORKERS% ^
    --worker-class uvicorn.workers.UvicornWorker ^
    --bind %HOST%:%PORT% ^
    --access-logfile - ^
    --error-logfile - ^
    --log-level info ^
    --timeout 120 ^
    --keepalive 5 ^
    --max-requests 1000 ^
    --max-requests-jitter 100

pause
