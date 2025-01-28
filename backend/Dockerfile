# Dockerfile used for local developement

FROM python:3.12-alpine3.17 as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_helloNO_CACHE_DIR=1 \
    POETRY_VERSION=1.3

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libpq-dev
RUN pip install --no-cache "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY proto /proto
RUN /venv/bin/python -m grpc_tools.protoc \
    -I../proto \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    ../proto/generated/*.proto

FROM base as final

WORKDIR /app

# migrations
COPY backend/manage.py .
COPY backend/migrations/ /app/migrations

COPY backend/scraper/models.py scraper/models.py
COPY backend/server.py backend/history.py backend/utility.py backend/weekly.py ./

EXPOSE 5000

CMD /venv/bin/python manage.py migrate && \
    /venv/bin/gunicorn -w 8 -b 0.0.0.0:8080 'server:app'
