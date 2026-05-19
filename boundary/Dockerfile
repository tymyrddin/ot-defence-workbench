FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables iproute2 \
    && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]