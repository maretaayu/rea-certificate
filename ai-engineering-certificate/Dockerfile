# Gunakan official image dari Microsoft Playwright (semua library OS untuk Chrome sudah terinstall)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Setting working directory
WORKDIR /app

# Copy requirement dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium untuk menjalankan konversi ke PDF. (Image ini sudah optimize untuk headless)
# Kita run install deps walaupun image official sudah cukup lengkap.
RUN playwright install chromium
RUN playwright install-deps

# Copy semua kode API & Template HTML
COPY . .

# Expose port yang digunakan
EXPOSE 8000

# Jalankan Uvicorn API Server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
