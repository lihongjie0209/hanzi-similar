#!/bin/bash

# 汉字相似度API生产环境启动脚本
# 使用venv创建虚拟环境，安装prod依赖并启动服务器

set -e  # 遇到错误时退出

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置参数
VENV_DIR="venv"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"

echo "🚀 汉字相似度API生产环境启动脚本"
echo "================================"

# 检查Python版本
echo "📋 检查Python版本..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python版本: $python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
else
    echo "📦 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装生产依赖
echo "📥 安装生产依赖..."
pip install --dependency-groups prod .

# 检查必要的目录和文件
echo "🔍 检查必要文件..."
if [ ! -f "api_main.py" ]; then
    echo "❌ 错误: api_main.py 文件不存在"
    exit 1
fi

if [ ! -d "chroma_db" ]; then
    echo "⚠️  警告: chroma_db 目录不存在，请确保已经构建了向量数据库"
fi

if [ ! -d "fonts" ]; then
    echo "⚠️  警告: fonts 目录不存在，SVG渲染功能可能不可用"
fi

# 显示启动信息
echo ""
echo "🌟 准备启动服务器..."
echo "主机: $HOST"
echo "端口: $PORT"
echo "工作进程数: $WORKERS"
echo ""

# 启动服务器
echo "🚀 启动Gunicorn服务器..."
exec gunicorn api_main:app \
    --workers "$WORKERS" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "$HOST:$PORT" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120 \
    --keepalive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100
