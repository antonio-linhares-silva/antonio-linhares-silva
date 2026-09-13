# Python 3.12 slim-bookworm, resolved from the official multi-platform index on 2026-09-13.
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS build
RUN pip install --no-cache-dir uv==0.12.13
WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
COPY --from=build /build/.venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DO_NOT_TRACK=1 \
    GIT_PYTHON_REFRESH=quiet
WORKDIR /work
ENTRYPOINT ["/opt/venv/bin/python", "-m", "geoai_portfolio.cli"]
