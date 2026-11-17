FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -U -r requirements.txt
COPY . .
ENV PORT=8000
EXPOSE 8000
# long timeout: a clip download can take 1–3 minutes
CMD gunicorn -b 0.0.0.0:$PORT -w 1 --threads 4 --timeout 300 app:app
