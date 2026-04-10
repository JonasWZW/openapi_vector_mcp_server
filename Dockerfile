FROM python:3.12-slim

WORKDIR /app

# Milvus Configuration
ENV MILVUS_HOST=localhost
ENV MILVUS_PORT=19530
ENV MILVUS_COLLECTION=openapi_vectors

# OpenAI Embeddings
ENV OPENAI_API_BASE_URL=https://api.siliconflow.cn/v1
ENV OPENAI_API_KEY=your-api-key-here
ENV OPENAI_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
ENV OPENAI_EMBEDDING_DIM=2560

# MCP Server
ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=15277


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 15277

ENTRYPOINT ["python", "mcp_server/server.py"]