# OpenAPI Vector MCP Server

基于 Milvus 向量数据库的 RAG 系统，用于检索 OpenAPI 接口文档。通过 MCP 协议提供语义搜索能力。

## 功能特性

- **fetch**: 从远程 URL 拉取 OpenAPI3 JSON 文档
- **wash**: 清洗 OpenAPI JSON，提取关键信息
- **vector**: 向量化存储到 Milvus，支持混合检索（dense + BM25）
- **MCP Server**: 提供 `list_collections`、`search_apis`、`get_api_detail` 三个工具

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_BASE_URL 和 OPENAI_API_KEY

# 2. 配置 OpenAPI 源
# 编辑 fetch.yaml，添加你的 OpenAPI JSON URL

# 3. 启动服务
docker-compose up -d

# 4. 运行 pipeline（拉取、清洗、向量化）
docker-compose exec mcp-server python pipeline.py
```

### 手动部署

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 运行 pipeline
python pipeline.py

# 启动 MCP Server
python mcp_server/server.py
```

## MCP 工具

| 工具 | 功能 | 参数 |
|------|------|------|
| `list_collections` | 列出所有 API 模块 | 无 |
| `search_apis` | 语义搜索 API | `collection`, `query`, `limit` |
| `get_api_detail` | 获取完整 API 信息 | `collection`, `uri` |

### 使用示例

```python
# 1. 列出所有模块
collections = list_collections()
# 返回: [{"collection": "example_api", "app_name": "example-api", "description": "..."}]

# 2. 搜索 API
results = search_apis(collection="example_api", query="创建用户", limit=3)
# 返回: [{"uri": "POST /innerService/users", "text": "..."}]

# 3. 获取详情
detail = get_api_detail(collection="example_api", uri="POST /innerService/users")
# 返回完整 API 信息：parameters, request, response 等
```

## 配置说明

### fetch.yaml

```yaml
apps:
  - app_name: my-api          # 应用名称（中文）
    collection_name: my_api   # Milvus collection 名称（英文）
    description: API 描述
    url: https://example.com/api-docs  # OpenAPI JSON URL
```

### .env

| 变量 | 说明 | 默认值 |
|------|------|--------|
| MILVUS_HOST | Milvus 地址 | localhost |
| MILVUS_PORT | Milvus 端口 | 19530 |
| OPENAI_API_BASE_URL | Embedding API 地址 | - |
| OPENAI_API_KEY | API 密钥 | - |
| OPENAI_EMBEDDING_MODEL | 模型名称 | Qwen/Qwen3-Embedding-4B |
| OPENAI_EMBEDDING_DIM | 向量维度 | 2560 |
| MCP_SERVER_PORT | MCP 服务端口 | 15277 |

## 技术栈

- **FastMCP**: MCP 协议实现（streamable-http）
- **Milvus**: 向量数据库（混合检索：dense + BM25 + RRF）
- **LangChain**: Embedding 集成
- **OpenAI-compatible API**: 支持 Qwen、SiliconFlow 等

## 目录结构

```
fetch/datas/      # 拉取的原始 OpenAPI JSON
docs/             # 清洗后的结构化 JSON
mcp_server/       # MCP Server 实现
vector/           # Milvus 客户端、Embedding
wash/             # OpenAPI 清洗逻辑
pipeline.py       # Pipeline 入口
fetch.yaml        # OpenAPI 源配置
```

## License

MIT