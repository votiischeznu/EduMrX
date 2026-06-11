FROM ghcr.io/astral-sh/uv:alpine
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY . .
CMD ["uv", "run", "gunicorn", "root.wsgi:application", "--bind", "0.0.0.0:8000"]
