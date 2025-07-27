FROM python:3.12-slim

# 環境
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# PIP
COPY requirements.txt .
RUN --mount=type=cache,target=~/.cache/pip \
    pip3 install -r requirements.txt

# APP
WORKDIR /workspace
COPY . .

# 複製腳本
COPY entrypoint.sh /entrypoint.sh
COPY clean-tmp.sh /usr/local/bin/clean-tmp.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/clean-tmp.sh

# 啟動
CMD ["/entrypoint.sh"]
