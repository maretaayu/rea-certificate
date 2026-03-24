"""
REA AI Engineering Certificate API (Pillow Version)
====================================
Endpoint untuk n8n via HTTP Request node.

POST /generate_cert
  Body (JSON):
    {
      "name"          : "Adrian Ananta",
      "student_id"    : "REAENG10RDFIR",
      "atc_accum"     : "100%",          // kolom Atc (Accum)
      "current_score" : 100,             // kolom Current Score
      "current_grade" : "A",
      "cert_type"     : "COC" | "COE" | "BEST"  // opsional, auto-detect jika tidak ada
    }

  Response:
    PNG binary (Content-Type: image/png)
    Header X-Cert-ID: REAENG10XXXXX
"""

import os
import io
import random
import string
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
BATCH          = "10"
ASSETS_DIR     = BASE_DIR / "assets"
TEMPLATE_COC   = ASSETS_DIR / "template_coc_blank.png"
TEMPLATE_COE   = ASSETS_DIR / "template_coe_blank.png"

FONT_PATH      = str(BASE_DIR / "Roboto-Bold.ttf")

try:
    font_name    = ImageFont.truetype(FONT_PATH, 110)
    font_desc    = ImageFont.truetype(FONT_PATH, 38)
    font_cert_id = ImageFont.truetype(FONT_PATH, 32)
except Exception:
    font_name = font_desc = font_cert_id = ImageFont.load_default()

# ─── APP ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "REA Certificate API",
    description = "Generate PNG certificates for AI Engineering Bootcamp Batch 10 via PIL (Vercel Serverless)",
    version     = "3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── MODELS ───────────────────────────────────────────────────────────────────
class CertRequest(BaseModel):
    name          : str
    student_id    : str
    atc_accum     : str             = "0%"
    current_score : str             = "0"
    current_grade : str             = ""
    cert_type     : Optional[str]   = None
    batch         : str             = BATCH

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def pct_to_float(val: str) -> float:
    val = str(val).strip()
    if val.endswith('%'):
        return float(val[:-1])
    try:
        f = float(val)
        if 0 < f <= 1.0:
            return f * 100
        return f
    except ValueError:
        return 0.0

def safe_float(val: str) -> float:
    try:
        return float(val)
    except ValueError:
        return 0.0

def make_cert_id(batch: str) -> str:
    chars = string.ascii_uppercase + string.digits
    return f"REAENG{batch}" + ''.join(random.choices(chars, k=5))

def draw_cert_image(
    cert_type_label: str,
    name: str,
    cert_id: str,
    atc_str: str,
    score: float,
    grade: str
) -> bytes:
    
    try:
        f_atc = float(atc_str)
        if 0 < f_atc <= 1.0:
            atc_str = f"{int(round(f_atc * 100))}%"
    except ValueError:
        pass

    if cert_type_label == "BEST":
        img_path = TEMPLATE_COE
        desc = (
            f"For demonstrating exceptional dedication, fulfilling all comprehensive curriculum requirements, "
            f"and successfully delivering an outstanding final project, thereby earning the status of "
            f"BEST STUDENT in the following program:"
        )
    elif cert_type_label == "COE":
        img_path = TEMPLATE_COE
        desc = (
            f"For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements "
            f"with a score of {int(score)}, thereby earning the grade of {grade} in the following program:"
        )
    else:  # COC
        img_path = TEMPLATE_COC
        desc = (
            f"For demonstrating strong commitment and successfully fulfilling the attendance requirements "
            f"with an accumulation score of {atc_str} throughout the sessions, thereby earning the status "
            f"of PASSED in the following program:"
        )

    # Buka gambar template
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Warna
    color_name = "#1e293b" # Slate-800
    color_desc = "#334155" # Slate-700
    color_cert = "#0284c7" # Light Blue
    
    # 1. Gambar Nama - Berada di bawah "IS PROUDLY AWARDED TO" (Y=560)
    name_pos = (260, 560)
    draw.text(name_pos, name, font=font_name, fill=color_name)

    # 2. Gambar Deskripsi - Tepat berada di bawah Nama, dan berada DI ATAS "Batch 10" (Y=720)
    desc_wrapped = textwrap.fill(desc, width=90)
    desc_pos = (265, 720)
    draw.multiline_text(desc_pos, desc_wrapped, font=font_desc, fill=color_desc, spacing=15)

    # 3. Gambar Credential ID (Pill inside HTML is drawn around Y=220-260).
    cert_id_pos = (2120, 245)
    draw.text(cert_id_pos, cert_id, font=font_cert_id, fill=color_cert, anchor="ra")

    # Export ke Bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()


# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "mode": "Pillow (PNG)"}


@app.post("/generate_cert/{filename}")
@app.post("/generate_cert")
def generate_cert(req: CertRequest, filename: Optional[str] = None, format: Optional[str] = None):
    atc_val   = pct_to_float(req.atc_accum)
    score_val = safe_float(req.current_score)
    cert_type = (req.cert_type or "").upper()

    if cert_type not in ("COC", "COE", "BEST"):
        if score_val >= 70:
            cert_type = "COE"
        elif atc_val >= 70:
            cert_type = "COC"
        else:
            raise HTTPException(status_code=400, detail="Student tidak memenuhi syarat")

    if cert_type == "COE" and score_val < 70:
        raise HTTPException(status_code=400, detail="COE requires Current Score >= 70")
    if cert_type == "COC" and atc_val < 70:
        raise HTTPException(status_code=400, detail="COC requires Atc (Accum) >= 70%")

    cert_id  = make_cert_id(req.batch)
    png_bytes = draw_cert_image(
        cert_type_label = cert_type,
        name            = req.name,
        cert_id         = cert_id,
        atc_str         = req.atc_accum,
        score           = score_val,
        grade           = req.current_grade,
    )

    filename = f"{req.name.replace(' ', '_')}_{cert_type}.png"
    if not filename.endswith('.png'):
        filename += '.png'
    
    if format == "json":
        import base64
        b64_str = base64.b64encode(png_bytes).decode("utf-8")
        return {
            "status": "success",
            "filename": filename,
            "cert_id": cert_id,
            "base64": b64_str
        }

    return Response(
        content      = png_bytes,
        media_type   = "image/png",
        headers      = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Cert-ID"          : cert_id,
            "X-Cert-Type"        : cert_type,
            "X-Student-Name"     : req.name,
        }
    )
