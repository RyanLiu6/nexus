FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tailscale_exporter.py .

EXPOSE 9199

CMD ["python", "tailscale_exporter.py"]
