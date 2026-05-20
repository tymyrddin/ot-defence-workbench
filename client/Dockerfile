FROM python:3.12-alpine
RUN pip install --no-cache-dir "pymodbus>=3.6,<3.7" "paho-mqtt>=1.6,<2.0" "asyncua" "cryptography>=48,<49"
COPY entrypoint.sh /entrypoint.sh
COPY read.py /app/read.py
COPY checks/ /checks/
COPY gen-opcua-cert.py /tmp/gen-opcua-cert.py
RUN python3 /tmp/gen-opcua-cert.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]