#!/bin/bash
set -e



# 确保字体目录存在
if [ ! -d "/app/fonts" ]; then
    echo "警告: fonts 目录不存在"
fi

# 启动应用
echo "启动 Gunicorn 服务器..."
exec "$@"
