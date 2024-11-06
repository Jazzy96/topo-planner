# 使用Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY src/ /app/src/
COPY requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（如果需要HTTP服务）
EXPOSE 8080

# 启动命令（如果需要HTTP服务）
CMD ["python", "-m", "src.server"] 