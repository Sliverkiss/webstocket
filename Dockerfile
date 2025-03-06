# 使用官方的 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的 requirements.txt 文件复制到容器中的 /app 目录
COPY requirements.txt /app/

# 安装项目所需的依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将你的 Python 脚本和 entrypoint.sh 脚本复制到容器中的 /app 目录
COPY server.py /app/
COPY client.py /app/
COPY entrypoint.sh /app/

# 给 entrypoint.sh 脚本可执行权限
RUN chmod +x /app/entrypoint.sh

# 设置容器的入口点为 entrypoint.sh 脚本
ENTRYPOINT ["/app/entrypoint.sh"]

# 外放端口（假设你的 HTTP 服务使用 5000 和 5001 端口）
EXPOSE 22115
EXPOSE 22116
EXPOSE 12218

