FROM python:3.11-slim

RUN useradd -m -u 1000 botuser

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# Mount a volume at /data so bot.db survives restarts
ENV DB_PATH=/data/bot.db
VOLUME /data
RUN mkdir -p /data && chown -R botuser:botuser /app /data

USER botuser

CMD ["python", "-m", "bot.main"]
