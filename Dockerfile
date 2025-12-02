FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
# Copy lock file if it exists
COPY uv.lock* ./

# Install dependencies (production only)
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy source code
COPY src/ ./src/

# Run the action
ENTRYPOINT ["uv", "run", "actions-advisor"]
