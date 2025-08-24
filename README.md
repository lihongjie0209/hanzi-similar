# Hanzi Similar Search | 相似汉字搜索

一个可本地运行/容器化的检索服务：将汉字渲染为图像，提取视觉向量，在向量库中检索“长得像”的字；提供 FastAPI 接口与简洁的 Web UI。

English: A FastAPI service to render Chinese characters, embed with ViT/CLIP, and search visually similar glyphs. Includes a clean web UI and SVG glyph rendering from local fonts.

## 功能特性
- 生成 CJK 字符图片（PNG，黑白）与可选的缺字报告
- 基于 ViT/CLIP 的图像向量（Transformers）+ ChromaDB 向量库
- FastAPI 检索接口（按字符或 Unicode）
- 前端页面 `/ui`（类 Google 风格），结果平铺，查询字置顶标记
- 后端使用本地字体实时渲染 SVG（`/glyph/svg/{UHEX}`），前端展示清晰无锯齿

## 运行要求
- Python 3.11+（建议使用 uv 作为依赖与运行器）
- 本地字体（ttf/otf/ttc/otc），放置到 `fonts/` 以覆盖需要的字形
- Windows、Linux、macOS 均可；Docker 可选

## 快速开始
方式一：本地运行（uv）

```sh
# 1) 可选：预先构建向量库（首次或变更后执行）
uv run python advanced_vectorizer.py

# 2) 启动服务（可用环境变量见下）
sh scripts/start.sh
```

Windows（PowerShell）直接运行 uvicorn：

```powershell
# 可选：构建向量库
uv run python .\advanced_vectorizer.py

# 启动 API（端口占用/权限问题可换 18080 等）
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

方式二：Docker 运行

```sh
docker build -t hanzi-similar:latest .
# 如果镜像未包含 fonts/chroma_db，请以只读或读写方式挂载
docker run --rm -p 18080:8000 \
  -e FONTS_DIR=/app/fonts \
  -e IMAGES_DIR=/app/images \
  -e CHROMA_DB_PATH=/app/chroma_db \
  -v "$PWD/fonts":/app/fonts:ro \
  -v "$PWD/images":/app/images:ro \
  -v "$PWD/chroma_db":/app/chroma_db \
  hanzi-similar:latest
```

打开页面：http://127.0.0.1:8000/ui/

## 环境变量（默认值）
- `IMAGES_DIR=images`：图片目录（可用于调试或备份）
- `CHROMA_DB_PATH=./chroma_db`：ChromaDB 数据目录
- `MODEL_NAME=google/vit-base-patch16-224`：Transformer 模型
- `TOP_K=10`：默认返回近邻数量
- `FONTS_DIR=fonts`：字体目录（后端渲染 SVG 使用）
- `HOST=0.0.0.0`，`PORT=8000`
- `BUILD_DB=0`：启动时是否重建向量库（设为 `1` 开启）

PowerShell 临时设置示例：

```powershell
$env:FONTS_DIR = "fonts"; $env:PORT = "18080"; uv run uvicorn api.main:app --host 127.0.0.1 --port $env:PORT
```

## 数据构建流程
1) 准备字体到 `fonts/`，保证覆盖目标字符区间；
2) 生成或校验图片（可选）：`uv run python generate_hanzi_images.py`；
3) 构建向量库（必需）：`uv run python advanced_vectorizer.py`；
4) 启动服务，前端/接口即可使用。

## API 文档与示例
- `POST /search/char`
  - 请求体：`{"char":"行","top_k":12}`
  - 返回：相似字列表（含字符、Unicode、距离/相似度等）

```bash
curl -s http://127.0.0.1:8000/search/char -H "Content-Type: application/json" \
  -d '{"char":"行","top_k":8}' | jq
```

- `POST /search/unicode`
  - 请求体：`{"unicode":"884C","top_k":12}`（不含 U+ 前缀）

- `GET /glyph/svg/{UHEX}`
  - 示例：`/glyph/svg/884C` 返回单字符 SVG，使用 `FONTS_DIR` 中可覆盖该码位的字体

> 前端页面 `/ui` 会直接调用以上接口，并将查询字置顶展示与标注。

## 字体说明
- 放置到 `fonts/`，支持 ttf/otf/ttc/otc；可多字体混合，后端会挑选可覆盖该码位的字体渲染；
- 若缺字，将返回 404 或错误信息；
- 字体版权需自理，请使用可分发/可部署许可的字体文件。

## 常见问题（Troubleshooting）
- 端口绑定失败（Windows 报 10013）：
  - 换端口（如 18080/18081），或避免绑定 0.0.0.0 用 127.0.0.1；
  - 确认无占用：`netstat -ano | findstr :8000`；必要时以管理员终端重试。
- 缺字/渲染失败：
  - 确认 `fonts/` 中有覆盖该字符的字体；
  - 可使用项目内检查脚本（如 `check_codepoint_coverage.py`）验证覆盖；
  - 使用另一款 CJK 覆盖更广的字体。
- 向量库很大（chroma_db）：
  - GitHub 对 >50MB 文件有提示，必要时使用 Git LFS 或不要提交该目录；
  - 也可在容器/运行环境中生成后持久化挂载。
- 模型/依赖下载慢：
  - 预下载脚本：`uv run python scripts/download_model.py`；
  - Dockerfile 已包含下载步骤，可在构建时完成。

## 开发与调试
- 运行开发服务器（热重载）：
  - `uv run uvicorn api.main:app --reload`
- 生成图片：
  - `uv run python generate_hanzi_images.py`
- 构建/更新向量库：
  - `uv run python advanced_vectorizer.py`
- 端到端快速验证：
  - 打开 `http://127.0.0.1:8000/ui/` 输入“行”等进行检索

## Docker 提示
- `.dockerignore` 已排除 `fonts/`，因此运行容器时请挂载字体目录；
- 如需将 `chroma_db` 一起打包，可在构建前准备好并 `COPY` 进镜像（当前 Dockerfile 已示例）。

## Linux systemd 部署
提供自动安装脚本：`scripts/install_systemd.sh`

```bash
# 安装并启动（需 root；脚本会尝试 sudo 提升）
bash scripts/install_systemd.sh install

# 查看状态
bash scripts/install_systemd.sh status

# 卸载服务
bash scripts/install_systemd.sh uninstall
```

- 脚本会生成环境文件：`/etc/hanzi-similar.env`，以及单位文件：`/etc/systemd/system/hanzi-similar.service`
- 默认使用仓库内 `scripts/start.sh` 启动；修改环境变量后执行 `sudo systemctl restart hanzi-similar`
- 查看日志：`journalctl -u hanzi-similar -f`

## 发布到 GitHub（可选）
使用 GitHub CLI（`gh`）：

```sh
gh repo create <owner>/<repo> --source . --private --disable-issues --disable-wiki
git add -A && git commit -m "feat: initial commit"
git branch -M main && git push -u origin main
```

## 备注
- 仅用于技术研究与学习，请注意字体与模型的授权条款；
- 欢迎提交 Issue/PR，或在 `README` 中补充适配的字体清单与示例结果。