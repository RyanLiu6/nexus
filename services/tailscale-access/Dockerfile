FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with gunicorn
# -w 4: 4 worker processes
# -b 0.0.0.0:8000: bind to port 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
