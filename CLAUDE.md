# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenAPI Vector MCP Server 是一个基于 Milvus 向量数据库的 RAG 系统，用于检索 OpenAPI 接口文档。支持从远程拉取 OpenAPI JSON、清洗、向量化存储，并通过 MCP 协议提供语义搜索能力。

## Architecture

```
fetch → wash → vector → MCP Server (search)
```

| Stage | Input | Output | Module |
|-------|-------|--------|--------|
| fetch | fetch.yaml (URLs) | fetch/datas/*.json | `fetch/fetch.py` |
| wash | fetch/datas/*.json | docs/*.json | `wash/wash_to_json.py` |
| vector | docs/*.json | Milvus collections | `vector/vectorize.py` |
| MCP Server | Milvus | Tool responses | `mcp_server/server.py` |

## Key Design Decisions

- **Per-app collection**: 每个 app 独立 Milvus collection，collection name 统一用英文（如 `bcm`、`dbbackup_manager`）
- **InnerService filter**: wash 阶段只处理路径包含 `innerService` 的 API（内部服务接口）
- **Lightweight search**: `search_apis` 只返回 `uri` + `text`（截断 500 字符），避免 token 膨胀；`get_api_detail` 获取完整信息
- **Hybrid search**: Milvus 混合检索（dense vector + sparse BM25），RRF 融合排序
- **Database isolation**: Milvus 使用 `restapi` 数据库隔离
- **Caching**: `list_collections` 2小时 TTL 缓存；`search_apis` per-collection 进程级缓存

## Directory Structure

```
fetch/raw/          # 原始 OpenAPI JSON（未使用）
fetch/datas/        # 拉取的 OpenAPI JSON 文件：{app_name}接口文档.json
docs/               # 清洗后的结构化 JSON：{app_name}.json
test/               # 手动测试脚本
```

## Configuration

环境变量通过 `.env` 配置（参考 `.env.example`）：

| Variable | Purpose | Default |
|----------|---------|---------|
| MILVUS_HOST | Milvus 服务地址 | localhost |
| MILVUS_PORT | Milvus 端口 | 19530 |
| OPENAI_API_BASE_URL | Embedding API 地址 | - |
| OPENAI_API_KEY | API 密钥 | - |
| OPENAI_EMBEDDING_MODEL | 模型名称 | Qwen/Qwen3-Embedding-4B |
| OPENAI_EMBEDDING_DIM | 向量维度 | 2560 |
| MCP_SERVER_PORT | MCP 服务端口 | 15277 |

App 配置在 `fetch.yaml`：`app_name`、`collection_name`（英文）、`description`、`url`。

## Common Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 完整 pipeline
python pipeline.py

# 单阶段运行
python pipeline.py --stage fetch   # 拉取 OpenAPI JSON
python pipeline.py --stage wash    # 清洗 JSON
python pipeline.py --stage vector  # 向量化到 Milvus

# 启动 MCP Server（streamable-http 协议）
python mcp_server/server.py

# 手动测试（调试 Milvus 连接）
python test/test.py
```

## MCP Tools

| Tool | Purpose | URI Format |
|------|---------|------------|
| `list_collections` | 列出所有 app 模块 | - |
| `search_apis` | 轻量搜索 | - |
| `get_api_detail` | 获取完整 API 信息 | `METHOD /path` |

**URI 格式**：`get_api_detail` 的 `uri` 参数格式为 `METHOD /path`，如 `POST /api/v1/users`。

## Vector Text Format

向量化文本格式（用于 embedding 和 BM25）：

```
[标签: tag1, tag2]。METHOD /path。功能：summary (operationId)。详细描述：description
```

## Apps (defined in fetch.yaml)

| App Name | Collection | Description |
|----------|------------|-------------|
| bcm | bcm | 节点生命周期治理与基础设施运维 |
| 存储管理 | dbbackup_manager | 数据备份恢复和存储资源配置管理 |
| 权限管理 | permission_manager | 认证授权与权限控制 |
| 消息通道 | message_channel | 消息通知订阅中心 |
| 系统告警 | system_alarm | 节点健康监控与告警运维 |
| 设备管理 | device_manager | 设备注册与管理 |
| 任务管理 | task_manager | 任务调度与生命周期管理 |

## Tech Stack

FastMCP (streamable-http), pymilvus (hybrid search), langchain (embeddings), OpenAI-compatible API (Qwen3-Embedding-4B)