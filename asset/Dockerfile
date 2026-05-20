FROM python:3.12-alpine
RUN apk add --no-cache mosquitto openssl && \
    pip install --no-cache-dir "pymodbus>=3.6,<3.7" "asyncua" "cryptography>=48,<49"
COPY entrypoint.sh /entrypoint.sh
COPY server.py /app/server.py
COPY mosquitto.conf /app/mosquitto.conf
COPY iec104frame.py /app/iec104frame.py
COPY iec104-server.py /app/iec104-server.py
COPY goose-server.py /app/goose-server.py
COPY modbus-tls-server.py /app/modbus-tls-server.py
COPY opcua-server.py /app/opcua-server.py
RUN mkdir /app/tls && \
    openssl req -x509 -newkey rsa:2048 \
        -keyout /app/tls/server.key -out /app/tls/server.crt \
        -days 3650 -nodes -subj "/CN=ot-asset"
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]