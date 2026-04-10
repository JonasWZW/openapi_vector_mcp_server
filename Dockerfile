FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 15277

ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=15277

CMD ["python", "mcp_server/server.py"]