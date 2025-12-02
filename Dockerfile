FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files and README (required by hatchling)
COPY pyproject.toml README.md ./
# Copy lock file if it exists
COPY uv.lock* ./
# Copy source code (needed before uv sync for package build)
COPY src/ ./src/

# Install dependencies (production only)
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Run the action using virtual environment Python
ENTRYPOINT [".venv/bin/python", "-m", "actions_advisor.main"]
