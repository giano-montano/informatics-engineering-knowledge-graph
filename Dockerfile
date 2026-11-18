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

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/app/.venv \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Las dependencias, en las versiones exactas de uv.lock. Esta capa solo cambia
# cuando cambia el archivo de bloqueo.
#
# IEKG_TORCH=cpu (por omisión) instala PyTorch y torchvision en esas mismas
# versiones, pero en su compilado solo para CPU, y deja fuera las bibliotecas
# de CUDA que el bloqueo trae en Linux: son varios gigabytes que un host sin
# GPU no usa. IEKG_TORCH=locked instala el bloqueo tal cual.
ARG IEKG_TORCH=cpu
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv \
    && if [ "$IEKG_TORCH" = "locked" ]; then \
         uv sync --frozen --no-dev --no-install-project; \
       else \
         uv export --frozen --no-dev --no-emit-project --no-hashes --no-annotate -o /tmp/locked.txt \
         && grep -v -E '^(nvidia-|cuda-|triton==|torch==|torchvision==)' /tmp/locked.txt > /tmp/rest.txt \
         && grep -E '^(torch|torchvision)==' /tmp/locked.txt > /tmp/torch.txt \
         && uv pip install --no-deps -r /tmp/rest.txt \
         && uv pip install --no-deps --index-url https://download.pytorch.org/whl/cpu -r /tmp/torch.txt \
         && rm /tmp/locked.txt /tmp/rest.txt /tmp/torch.txt; \
       fi

COPY src ./src
COPY ontology ./ontology
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps -e .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["iekg-api"]
