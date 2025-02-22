# Gunakan Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY . .

# Expose port yang digunakan Gunicorn
EXPOSE 8000

# Command untuk menjalankan Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "scrapp.wsgi:app"]
