# Python 3.12 slim-bookworm, resolved from the official multi-platform index on 2026-09-13.
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS build
RUN pip install --no-cache-dir uv==0.12.13
WORKDIR /build
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DO_NOT_TRACK=1 \
    GIT_PYTHON_REFRESH=quiet
WORKDIR /work
ENTRYPOINT ["/opt/venv/bin/python", "-m", "geoai_portfolio.cli"]
