# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建日志目录并设置适当的权限
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs && \
    mkdir -p /var/log/topo-planner && \
    chmod 777 /var/log/topo-planner && \
    mkdir -p /app/static && \
    mkdir -p /app/results && \
    chmod 777 /app/results 

# 复制源代码
COPY src/ ./src/
COPY static/ ./static/

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.server"]
