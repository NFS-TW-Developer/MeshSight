#!/bin/sh

# 背景執行清理 /tmp 的迴圈，每 10 分鐘一次
while true; do
    /usr/local/bin/clean-tmp.sh
    sleep 600
done &

# 先執行 config 初始化
python3 -m app.init_config

# 等待秒
sleep 5

# 啟動主應用程式
exec python3 -m app
