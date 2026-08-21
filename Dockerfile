FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

RUN mkdir -p data

# One worker on purpose: the session cache in auth.py is per-process, and with
# several workers a revocation would take up to CACHE_TTL to reach the others
# (SPEC.md §12). Two vCPUs and a gate that does one SQLite read per request do
# not need more.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8019", "--workers", "1"]
