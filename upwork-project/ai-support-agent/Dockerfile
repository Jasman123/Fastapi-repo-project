# ── Stage 1: dependency install ──────────────────────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for GCP Cloud Run security best practice
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy source
COPY app/ ./app/

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
EXPOSE 8080

USER appuser

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"]
