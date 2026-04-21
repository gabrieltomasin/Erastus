FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" --extra-index-url https://download.pytorch.org/whl/cpu || \
    pip install --no-cache-dir -e ".[dev]"

COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
