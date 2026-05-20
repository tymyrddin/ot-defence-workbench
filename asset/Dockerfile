FROM python:3.12-alpine
RUN apk add --no-cache mosquitto && \
    pip install --no-cache-dir "pymodbus>=3.6,<3.7"
COPY entrypoint.sh /entrypoint.sh
COPY server.py /app/server.py
COPY mosquitto.conf /app/mosquitto.conf
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]