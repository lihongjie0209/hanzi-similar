#!/bin/bash
set -e

# 确保 chroma_db 目录存在且有正确权限
if [ ! -d "/app/chroma_db" ]; then
    echo "创建 chroma_db 目录..."
    mkdir -p /app/chroma_db
fi

# 设置正确的权限
chmod -R 755 /app/chroma_db
chown -R $(id -u):$(id -g) /app/chroma_db

# 确保字体目录存在
if [ ! -d "/app/fonts" ]; then
    echo "警告: fonts 目录不存在"
fi

# 启动应用
echo "启动 Gunicorn 服务器..."
exec "$@"
