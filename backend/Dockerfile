# ---- Stage 1: Builder ----
FROM python:3.10-slim as builder

WORKDIR /install

# sirf build ke liye deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# wheels build karo (fast + reusable)
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps -r requirements.txt

# ---- Stage 2: Final ----
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# runtime deps only (minimal)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# wheels copy karo
COPY --from=builder /install /install

# install from wheels (fast + clean)
RUN pip install --no-cache-dir /install/*

# app code last
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
