FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# Mount a volume at /data so bot.db survives restarts
ENV DB_PATH=/data/bot.db
VOLUME /data

CMD ["python", "-m", "bot.main"]
