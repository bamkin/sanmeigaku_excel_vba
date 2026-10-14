# 六十の風景 — Railway 用（無料診断・申込〜承認〜送付・PDF を一つのプロセスで）
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 libffi8 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
# Noto Serif JP（取れなくても fonts-noto-cjk の明朝で動く）
RUN python scripts/get_fonts.py || echo "fonts: fallback to Noto Serif CJK JP"

ENV PORT=8000
CMD ["sh", "-c", "uvicorn shindan.app:app --host 0.0.0.0 --port ${PORT}"]
