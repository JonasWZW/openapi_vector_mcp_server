# OpenAPI Vector MCP Server

基于 Milvus 向量数据库的 RAG 系统，用于检索 OpenAPI 接口文档。通过 MCP 协议提供语义搜索能力。

## 功能特性

- **fetch**: 从远程 URL 拉取 OpenAPI3 JSON 文档
- **wash**: 清洗 OpenAPI JSON，提取关键信息
- **vector**: 向量化存储到 Milvus，支持混合检索（dense + BM25）
- **MCP Server**: 提供 `list_collections`、`search_apis`、`get_api_detail` 三个工具

## 快速开始

### Docker 部署

```bash
# 构建镜像
docker build -t openapi-vector-mcp .

# 启动 MCP Server
docker run -d -p 15277:15277 \
  -e MILVUS_HOST=your-milvus-host \
  -e OPENAI_API_KEY=your-api-key \
  openapi-vector-mcp

# 运行 Pipeline（可选，用于初始化数据）
docker run --rm \
  -e MILVUS_HOST=your-milvus-host \
  -e OPENAI_API_KEY=your-api-key \
  -v ./fetch.yaml:/app/fetch.yaml \
  openapi-vector-mcp \
  python pipeline.py
```

### 本地部署

```bash
pip install -r requirements.txt
python pipeline.py
python mcp_server/server.py
```

## MCP 工具

| 工具 | 功能 | 参数 |
|------|------|------|
| `list_collections` | 列出所有 API 模块 | 无 |
| `search_apis` | 语义搜索 API | `collection`, `query`, `limit` |
| `get_api_detail` | 获取完整 API 信息 | `collection`, `uri` |

## 配置

### fetch.yaml

```yaml
apps:
  - app_name: my-api
    collection_name: my_api
    description: API 描述
    url: https://example.com/api-docs
```

### 环境变量

| 变量 | 默认值 |
|------|--------|
| MILVUS_HOST | localhost |
| MILVUS_PORT | 19530 |
| MILVUS_COLLECTION | openapi_vectors |
| OPENAI_API_BASE_URL | https://api.siliconflow.cn/v1 |
| OPENAI_API_KEY | your-api-key-here |
| OPENAI_EMBEDDING_MODEL | Qwen/Qwen3-Embedding-4B |
| OPENAI_EMBEDDING_DIM | 2560 |
| MCP_SERVER_HOST | 0.0.0.0 |
| MCP_SERVER_PORT | 15277 |

## 目录结构

```
fetch/         # 拉取 OpenAPI JSON
wash/          # 清洗逻辑
vector/        # Milvus 客户端、Embedding
mcp_server/    # MCP Server 实现
docs/          # 清洗后的 JSON
pipeline.py    # Pipeline 入口
fetch.yaml     # OpenAPI 源配置
```

## MCP 客户端配置

本项目使用 `streamable-http` 协议，启动后在 `http://localhost:15277/mcp` 提供服务。

### Claude Desktop / Cursor / VS Code

在 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "openapi-vector": {
      "url": "http://localhost:15277/mcp"
    }
  }
}
```

### Docker 部署后连接

```json
{
  "mcpServers": {
    "openapi-vector": {
      "url": "http://your-server-ip:15277/mcp"
    }
  }
}
```

### 配置文件位置

| 客户端 | 配置文件路径 |
|--------|--------------|
| Claude Desktop | `~/.claude/claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |
| VS Code (Copilot) | `.vscode/mcp.json` |

## 技术栈

FastMCP (streamable-http) / Milvus (hybrid search) / LangChain / OpenAI-compatible API
