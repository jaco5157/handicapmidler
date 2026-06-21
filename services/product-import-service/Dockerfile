FROM cgr.dev/chainguard/python:latest-dev

USER root

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    CHROME_BIN=/usr/bin/chromium \
    SELENIUM_DRIVER_PATH=/usr/bin/chromedriver \
    PIP_BREAK_SYSTEM_PACKAGES=1

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    chromium \
    font-freefont \
    libjpeg-dev \
    libwebp-dev \
    zlib-dev

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN chown -R nonroot:nonroot /app

USER nonroot

EXPOSE 8000

ENTRYPOINT []
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
