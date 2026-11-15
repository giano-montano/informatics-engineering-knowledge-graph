# Imagen única de la aplicación: la API, el worker de ingesta y los procesos
# de construcción salen de aquí, con tres puntos de entrada (ADR-007).
#   iekg-api      la API, que lanza el worker como proceso hijo
#   iekg-worker   el worker, que la API ejecuta con `python -m`
#   iekg-build    los procesos de construcción (`docker compose run --rm build load`)
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /bin/uv

# Lo que piden en tiempo de ejecución las dependencias de lectura de PDF.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero las dependencias, tal como las fija uv.lock: esta capa solo cambia
# cuando cambia el archivo de bloqueo.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY ontology ./ontology
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["iekg-api"]
