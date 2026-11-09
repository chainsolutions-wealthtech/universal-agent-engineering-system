FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UAES_DB=/data/uaes.sqlite
WORKDIR /app
RUN groupadd -r uaes && useradd -r -g uaes -d /app uaes && mkdir -p /data && chown uaes:uaes /data
COPY src ./src
USER uaes
VOLUME ["/data"]
EXPOSE 8080
CMD ["python","-m","src.daemon"]
