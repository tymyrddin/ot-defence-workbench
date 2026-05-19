FROM python:3.12-alpine
RUN pip install --no-cache-dir "pymodbus>=3.6,<3.7"
COPY entrypoint.sh /entrypoint.sh
COPY read.py /app/read.py
COPY checks/ /checks/
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]