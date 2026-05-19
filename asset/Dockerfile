FROM python:3.12-alpine
RUN pip install --no-cache-dir "pymodbus>=3.6,<3.7"
COPY entrypoint.sh /entrypoint.sh
COPY server.py /app/server.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]