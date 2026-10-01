FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
RUN useradd --create-home --shell /usr/sbin/nologin oncojev \
    && mkdir -p /app /work/director \
    && chown oncojev:oncojev /work/director
WORKDIR /app
COPY --chmod=755 . .
ENV HOME=/home/oncojev UV_CACHE_DIR=/tmp/uv-cache PATH="/app/.venv/bin:$PATH"
RUN uv sync --frozen --no-dev
RUN chmod a-w /app \
    && mkdir -p /app/var/workspaces \
    && chown -R oncojev:oncojev /app/var
USER oncojev
CMD ["python", "-m", "src", "serve"]
