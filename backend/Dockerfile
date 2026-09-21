FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and generate requirements, then install
COPY backend/pyproject.toml /tmp/pyproject.toml
RUN python -c "import tomllib; f=open('/tmp/pyproject.toml','rb'); d=tomllib.load(f); deps=d['project']['dependencies']; dev=d['project'].get('optional-dependencies',{}).get('dev',[]); open('/tmp/requirements.txt','w').write('\n'.join(deps+dev))" \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy services.yaml for seeding
COPY simulators/services.yaml /app/services.yaml

# Copy backend application code
COPY backend/ ./

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
