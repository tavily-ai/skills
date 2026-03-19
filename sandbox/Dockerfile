# tvly-filter-sandbox
#
# Build:  docker build -t tvly-filter-sandbox sandbox/
# Test:   docker run --rm -e TAVILY_API_KEY -e ANTHROPIC_API_KEY \
#           tvly-filter-sandbox "test query" --verbose
#
# The ENTIRE filter agent runs inside this container:
#   - LLM calls (Anthropic/OpenAI API)
#   - Tavily search/extract API calls
#   - Python code the agent writes + executes
# The host just does `docker run` and reads stdout.

FROM python:3.12-slim

# System deps for lxml / parsing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libxml2 libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project definition first (layer cache for deps)
COPY pyproject.toml /app/pyproject.toml

# Install dependencies (cached unless pyproject.toml changes)
RUN cd /app && uv pip install --system --no-cache .

# Copy source code
COPY src/ /app/src/

# Re-install to pick up the actual package code
RUN cd /app && uv pip install --system --no-cache --no-deps .

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["tvly-filter"]
