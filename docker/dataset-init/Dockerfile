# dataset-init service
# Phase 0: minimal placeholder that exits 0 so Docker Compose can start.
# Phase 1 will implement Kaggle download + PostgreSQL import.

FROM python:3.12-slim

WORKDIR /app

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
