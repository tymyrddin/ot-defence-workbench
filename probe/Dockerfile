FROM python:3.12-alpine
RUN pip install --no-cache-dir "pymodbus>=3.6,<4"
COPY entrypoint.sh /entrypoint.sh
COPY checks/ /checks/
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]