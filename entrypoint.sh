#!/bin/bash
# 启动 server.py
python /app/server.py &

# 启动 client.py
python /app/client.py &

# 保持容器运行
tail -f /dev/null
