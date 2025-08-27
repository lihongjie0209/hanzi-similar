# API 文档查看指南

## 🔍 GitHub 对 OpenAPI 文档的支持

GitHub **不能直接预览** OpenAPI/Swagger 文档，但有以下几种查看方式：

### 1. 在线 Swagger UI 预览 ⭐ 推荐
```
https://petstore.swagger.io/?url=https://raw.githubusercontent.com/lihongjie0209/hanzi-similar/master/openapi.yaml
```

### 2. GitHub Pages 部署
可以创建 GitHub Pages 来托管 Swagger UI：
```yaml
# .github/workflows/docs.yml
name: Deploy API Docs
on:
  push:
    branches: [ master ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

### 3. 本地查看
启动 API 服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4. VS Code 扩展
推荐安装以下 VS Code 扩展来预览 OpenAPI 文档：
- **Swagger Viewer**: 直接在 VS Code 中预览
- **OpenAPI (Swagger) Editor**: 编辑和预览 OpenAPI 规范

### 5. 在线工具
- [Swagger Editor](https://editor.swagger.io/): 在线编辑和预览
- [Redoc Demo](https://redocly.github.io/redoc/): 更美观的文档展示
- [Insomnia](https://insomnia.rest/): API 测试工具，支持导入 OpenAPI

## 📋 当前 API 端点概览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 重定向到 Web UI |
| `/healthz` | GET | 健康检查 |
| `/search/char` | POST | 按字符搜索相似汉字 |
| `/search/unicode` | POST | 按 Unicode 搜索 |
| `/search/batch/char` | POST | 批量字符搜索 |
| `/search/batch/unicode` | POST | 批量 Unicode 搜索 |
| `/glyph/svg/{uhex}` | GET | 生成 SVG 字形 |

## 🛠️ API 测试工具

### cURL 示例
```bash
# 搜索相似字符
curl -X POST "http://localhost:8000/search/char" \
  -H "Content-Type: application/json" \
  -d '{"char": "中", "top_k": 5}'

# 批量搜索
curl -X POST "http://localhost:8000/search/batch/char" \
  -H "Content-Type: application/json" \
  -d '{"chars": ["中", "国"], "top_k": 3}'
```

### Python 示例
```python
import requests
import json

# 单字符搜索
response = requests.post("http://localhost:8000/search/char", 
                        json={"char": "中", "top_k": 5})
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# 批量搜索
response = requests.post("http://localhost:8000/search/batch/char",
                        json={"chars": ["中", "国", "人"], "top_k": 3})
results = response.json()
```

### JavaScript 示例
```javascript
// 使用 fetch API
async function searchSimilar(char, topK = 5) {
  const response = await fetch('http://localhost:8000/search/char', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ char, top_k: topK })
  });
  return await response.json();
}

// 调用示例
searchSimilar('中', 5).then(data => console.log(data));
```
