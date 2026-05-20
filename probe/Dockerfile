FROM python:3.12-alpine
RUN apk add --no-cache iproute2 && \
    pip install --no-cache-dir "pymodbus>=3.6,<3.7" "paho-mqtt>=1.6,<2.0" "asyncua" "cryptography>=48,<49"
COPY entrypoint.sh /entrypoint.sh
COPY checks/ /checks/
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]