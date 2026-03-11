from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import io

app = FastAPI(title="REA AI Engineering Certificate API")

# Setup Request Body Model yang akan diterima dari n8n
class CertRequest(BaseModel):
    nama: str
    sesi: str     # Contoh: "S1" / "S2" / "S3"
    urutan: str   # Contoh: "1" / "050" / "073"
    status: str = "PASSED"
    batch: str = "9"  # Default to 9
# ============== KONFIGURASI ===================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "index.html")

app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "../assets")), name="assets")

SESSIONS = {
    "S1": {
        "event_date_no": "28022026",
        "cert_date": "Jakarta, 7 Maret 2026",
        "topic": "Getting Started as an AI Engineer: Career Paths, Portfolios, and Interviews"
    },
    "S2": {
        "event_date_no": "07032026",
        "cert_date": "Jakarta, 14 Maret 2026",
        "topic": "Practical AI Automation with N8N for Real-World Workflows"
    },
    "S3": {
        "event_date_no": "14032026",
        "cert_date": "Jakarta, 21 Maret 2026",
        "topic": "Vibe Coding: From Zero to End-to-End Full-Stack Application with AI"
    }
}
# ===============================================

@app.get("/")
def home():
    return {"message": "API Sertifikat REA AI Engineering Running. Gunakan POST atau GET /generate_cert"}

@app.get("/generate_cert")
def generate_cert(nama: str, sesi: str, urutan: str, status: str = "PASSED", batch: str = "9"):
    # Ekstrak Sesi berdasarkan teks
    sesi_raw = sesi.upper()
    if "SESI 1" in sesi_raw:
        sesi_key = "S1"
    elif "SESI 2" in sesi_raw:
        sesi_key = "S2"
    elif "SESI 3" in sesi_raw:
        sesi_key = "S3"
    else:
        # Fallback kalau format tidak dikenali
        sesi_key = sesi_raw

    if sesi_key not in SESSIONS:
        raise HTTPException(status_code=400, detail=f"Sesi '{sesi}' tidak dikenali. Harus mengandung kata 'Sesi 1', 'Sesi 2', atau 'Sesi 3'.")

    # Validasi Template
    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(status_code=500, detail="Template HTML tidak ditemukan di server.")

    # Data dari request
    nama = nama.strip()
    urutan = urutan.strip().zfill(3)
    sesi_info = SESSIONS[sesi_key]
    
    event_date_no = sesi_info["event_date_no"]
    cert_date = sesi_info["cert_date"]
    topik = sesi_info["topic"]
    
    no_sertifikat = f"REA/{event_date_no}/{sesi_key}/{urutan}"

    # Load Template
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Render Template
    html_content = html_content.replace("{{NAMA}}", nama)
    html_content = html_content.replace("{{TOPIK}}", topik)
    html_content = html_content.replace("{{TANGGAL}}", cert_date)
    html_content = html_content.replace("{{NO_SERTIFIKAT}}", no_sertifikat)
    
    # Status styling
    html_content = html_content.replace("{{STATUS}}", status.upper())
    css_class = "status-best" if status.upper() == "BEST STUDENT" else "status-passed"
    html_content = html_content.replace("{{STATUS_CLASS}}", css_class)
    
    # Batch Replace
    html_content = html_content.replace("{{BATCH}}", batch)

    # Return as HTML so it can be converted to PDF via Puppeteer / Playwright in n8n or externally
    return Response(content=html_content, media_type="text/html")
