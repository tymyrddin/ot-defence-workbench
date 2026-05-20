FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables iproute2 python3 \
    && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /entrypoint.sh
COPY goose-relay.py /app/goose-relay.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]