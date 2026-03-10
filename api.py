from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import os
import io

app = FastAPI(title="REA Certificate Generator API")

# Setup Request Body Model yang akan diterima dari n8n
class CertRequest(BaseModel):
    nama: str
    sesi: str     # Contoh: "S1" / "S2" / "S3"
    urutan: str   # Contoh: "1" / "050" / "073"

# ============== KONFIGURASI ===================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "assets", "template_clean.jpg")
SIGNATURE_PATH_1 = os.path.join(BASE_DIR, "assets", "TTD dan Cap-01.png") # TTD
SIGNATURE_PATH_2 = os.path.join(BASE_DIR, "assets", "cap-rg.png") # Cap
FONT_PATH = os.path.join(BASE_DIR, "Roboto-Bold.ttf")

SESSIONS = {
    "S1": {
        "event_date_no": "28022026",
        "cert_date": "Jakarta, 7 Maret 2026",
        "topic": "Getting Started as an AI Engineer:\nCareer Paths, Portfolios, and Interviews"
    },
    "S2": {
        "event_date_no": "07032026",
        "cert_date": "Jakarta, 14 Maret 2026",
        "topic": "Practical AI Automation with N8N\nfor Real-World Workflows"
    },
    "S3": {
        "event_date_no": "14032026",
        "cert_date": "Jakarta, 21 Maret 2026",
        "topic": "Vibe Coding: From Zero to End-to-End\nFull-Stack Application with AI"
    }
}

POS_NAMA = (1754, 1000)
POS_TOPIK = (1754, 1460)
POS_TANGGAL = (1754, 1720)
POS_NOMOR = (3200, 2330)

FONT_NAMA_SIZE = 120
FONT_TOPIK_SIZE = 75
FONT_TANGGAL_SIZE = 60
FONT_NOMOR_SIZE = 55

FONT_NAMA_COLOR = "#000000"
FONT_TOPIK_COLOR = "#000000"
FONT_TEXT_COLOR = "#000000"
FONT_NOMOR_COLOR = "#000000"
# ===============================================

def load_fonts():
    try:
        font_nama = ImageFont.truetype(FONT_PATH, FONT_NAMA_SIZE)
        font_topik = ImageFont.truetype(FONT_PATH, FONT_TOPIK_SIZE)
        font_tanggal = ImageFont.truetype(FONT_PATH, FONT_TANGGAL_SIZE)
        font_nomor = ImageFont.truetype(FONT_PATH, FONT_NOMOR_SIZE)
        return font_nama, font_topik, font_tanggal, font_nomor
    except Exception as e:
        print("Gagal load font:", e)
        return (ImageFont.load_default(),) * 4

@app.get("/")
def home():
    return {"message": "API Sertifikat REA Running. Gunakan POST /generate_cert"}

@app.get("/generate_cert")
def generate_cert(nama: str, sesi: str, urutan: str):
    # Ekstrak Sesi berdasarkan teks (karena dari G-Form teksnya panjang "Sesi 1 (28 Feb)...")
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
        raise HTTPException(status_code=500, detail="Template gambar tidak ditemukan di server.")

    # Data dari request
    nama = nama.strip()
    urutan = urutan.strip().zfill(3)
    sesi_info = SESSIONS[sesi_key]
    
    event_date_no = sesi_info["event_date_no"]
    cert_date = sesi_info["cert_date"]
    topik = sesi_info["topic"]
    
    no_sertifikat = f"REA/{event_date_no}/{sesi_key}/{urutan}"

    # Load Template
    try:
        base_template = Image.open(TEMPLATE_PATH).convert("RGBA")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memuat template: {str(e)}")

    fonts = load_fonts()

    # Buat kanvas gambar
    temp_image = Image.new("RGBA", base_template.size)
    temp_image.paste(base_template, (0, 0))
    draw = ImageDraw.Draw(temp_image)

    # Tulis teks
    draw.text(POS_NAMA, nama, font=fonts[0], fill=FONT_NAMA_COLOR, anchor="mm")
    draw.text(POS_TOPIK, topik, font=fonts[1], fill=FONT_TOPIK_COLOR, anchor="mm", align="center")
    draw.text(POS_TANGGAL, cert_date, font=fonts[2], fill=FONT_TEXT_COLOR, anchor="mm")
    draw.text(POS_NOMOR, no_sertifikat, font=fonts[3], fill=FONT_NOMOR_COLOR, anchor="mm")

    # Tempel Tandatangan & Cap (Ditumpuk)
    try:
        # 1. Tempel Cap (Layer bawah)
        if os.path.exists(SIGNATURE_PATH_2):
             cap_img = Image.open(SIGNATURE_PATH_2).convert("RGBA")
             # Ukuran cap lebih dibesarkan (lebar sekitar 400px)
             w_percent = (400 / float(cap_img.size[0]))
             h_size = int((float(cap_img.size[1]) * float(w_percent)))
             cap_img = cap_img.resize((400, h_size), Image.Resampling.LANCZOS)
             
             # Digeser ke tengah persis sejajar dengan TTD
             pos_x = 1754 - (cap_img.size[0] // 2)
             pos_y = 1820 # Digeser lebih ke bawah menghindari numpuk parah di atas
             temp_image.paste(cap_img, (pos_x, pos_y), mask=cap_img)
             
        # 2. Tempel TTD (Layer atas)
        if os.path.exists(SIGNATURE_PATH_1):
             sign_img = Image.open(SIGNATURE_PATH_1).convert("RGBA")
             w_percent = (450 / float(sign_img.size[0]))
             h_size = int((float(sign_img.size[1]) * float(w_percent)))
             sign_img = sign_img.resize((450, h_size), Image.Resampling.LANCZOS)
             
             pos_x = 1754 - (sign_img.size[0] // 2)
             pos_y = 1780 # Koordinat sama persis agar menumpuk sejajar
             temp_image.paste(sign_img, (pos_x, pos_y), mask=sign_img)
             
    except Exception as e:
        print(f"Gagal paste tanda tangan & cap: {e}")

    # Konversi ke RGB dan simpan ke buffer memori
    final_image = temp_image.convert("RGB")
    buf = io.BytesIO()
    final_image.save(buf, format="JPEG", quality=95)
    buf.seek(0)

    # Kembalikan gambar langsung sebagai Response
    # Di n8n nanti, node HTTP Request otomatis mendownload ini sebagai File Binary
    return Response(content=buf.getvalue(), media_type="image/jpeg", headers={"Content-Disposition": f'attachment; filename="{no_sertifikat}.jpg"'})
