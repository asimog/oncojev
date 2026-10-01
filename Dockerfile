FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
RUN useradd --create-home --shell /usr/sbin/nologin oncojev \
    && mkdir -p /app /tmp/oncojev-coder \
    && chown -R oncojev:oncojev /app /tmp/oncojev-coder
WORKDIR /app
COPY --chown=oncojev:oncojev . .
USER oncojev
ENV HOME=/home/oncojev UV_CACHE_DIR=/tmp/uv-cache PATH="/app/.venv/bin:$PATH"
RUN uv sync --frozen --no-dev
CMD ["python", "-m", "src", "serve"]
