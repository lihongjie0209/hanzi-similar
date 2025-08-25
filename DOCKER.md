# 汉字相似度API - Docker部署

## 快速开始

使用Docker从Docker Hub运行汉字相似度API：

```bash
# 运行最新版本
docker run -p 8000:8000 lihongjie0209/hanzi-similar:latest

# 访问API文档
open http://localhost:8000/docs
```

## 可用标签

- `latest` - 最新版本
- `v0.1.0` - 稳定版本 0.1.0

## 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `CHROMA_DB_PATH` | `/app/chroma_db` | ChromaDB数据库路径 |
| `FONTS_DIR` | `/app/fonts` | 字体文件目录 |
| `TOP_K` | `10` | 默认返回相似字符数量 |
| `MODEL_NAME` | `google/vit-base-patch16-224` | 使用的AI模型 |

## 端点

- `GET /` - 重定向到Web界面
- `GET /docs` - API文档
- `GET /healthz` - 健康检查
- `POST /search/char` - 按字符搜索相似汉字
- `POST /search/unicode` - 按Unicode编码搜索
- `GET /glyph/svg/{unicode}` - 生成字符SVG图像

## 示例

```bash
# 健康检查
curl http://localhost:8000/healthz

# 搜索相似字符
curl -X POST http://localhost:8000/search/char \
  -H "Content-Type: application/json" \
  -d '{"char": "中", "top_k": 5}'

# 生成SVG字形
curl http://localhost:8000/glyph/svg/4E2D -o zhong.svg
```

## 生产部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  hanzi-similar:
    image: lihongjie0209/hanzi-similar:latest
    ports:
      - "8000:8000"
    environment:
      - TOP_K=20
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 镜像信息

- **基础镜像**: `python:3.13-slim`
- **镜像大小**: ~1.54GB
- **架构**: `linux/amd64`
- **包含**: 预训练模型、字体文件、向量数据库

## 源码

- **GitHub**: https://github.com/lihongjie0209/hanzi-similar
- **Docker Hub**: https://hub.docker.com/r/lihongjie0209/hanzi-similar
