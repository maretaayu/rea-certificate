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
from typing import Optional, Union

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
BATCH          = "10"
ASSETS_DIR     = BASE_DIR / "assets"
TEMPLATE_COC   = ASSETS_DIR / "template_coc_blank.png"
TEMPLATE_COE   = ASSETS_DIR / "template_coe_blank.png"

FONT_PATH_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
FONT_PATH_REG  = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

try:
    font_name    = ImageFont.truetype(FONT_PATH_BOLD, 110)
    font_desc_reg= ImageFont.truetype(FONT_PATH_REG, 38)
    font_desc_bld= ImageFont.truetype(FONT_PATH_BOLD, 38)
    font_cert_id = ImageFont.truetype(FONT_PATH_BOLD, 32)
except Exception:
    font_name = font_desc_reg = font_desc_bld = font_cert_id = ImageFont.load_default()

def draw_rich_text(draw, pos, text, font_reg, font_bold, fill_color, max_w_chars=85, spacing=15):
    words = text.split(' ')
    lines = []
    current_line = []
    current_len = 0
    for word in words:
        clean = word.replace('<b>', '').replace('</b>', '')
        if current_len + len(clean) + 1 > max_w_chars and current_line:
            lines.append(current_line)
            current_line = [word]
            current_len = len(clean)
        else:
            current_line.append(word)
            current_len += len(clean) + 1
    if current_line:
        lines.append(current_line)
        
    x_start, y = pos
    is_bold = False
    for line in lines:
        x = x_start
        for word in line:
            was_bold = is_bold
            if '<b>' in word:
                is_bold = True
                was_bold = True
                word = word.replace('<b>', '')
            if '</b>' in word:
                is_bold = False
                word = word.replace('</b>', '')
            font = font_bold if was_bold else font_reg
            draw.text((x, y), word, font=font, fill=fill_color)
            x += draw.textlength(word + ' ', font=font)
        y += 38 + spacing

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
    student_id    : Union[str, int]
    atc_accum     : Union[str, int, float] = "0%"
    current_score : Union[str, int, float] = "0"
    current_grade : Union[str, int, float] = ""
    cert_type     : Optional[str]          = None
    batch         : Union[str, int]        = BATCH

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
            f"<b>BEST STUDENT</b> in the following program:"
        )
    elif cert_type_label == "COE":
        img_path = TEMPLATE_COE
        desc = (
            f"For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements "
            f"with a score of <b>{int(score)}</b>, thereby earning the grade of <b>{grade}</b> in the following program:"
        )
    else:  # COC
        img_path = TEMPLATE_COC
        desc = (
            f"For demonstrating strong commitment and successfully fulfilling the attendance requirements "
            f"with an accumulation score of <b>{atc_str}</b> throughout the sessions, thereby earning the status "
            f"of <b>PASSED</b> in the following program:"
        )

    # Buka gambar template
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Warna
    color_name = "#1e293b" # Slate-800
    color_desc = "#334155" # Slate-700
    color_cert = "#0284c7" # Light Blue
    
    # 1. Gambar Nama - (Dikembalikan ke Y=600 biar nempel dan nyambung dengan title Awarded To)
    name_pos = (260, 600)
    draw.text(name_pos, name, font=font_name, fill=color_name)

    # 2. Gambar Deskripsi - (Rich Text dg Bold)
    desc_pos = (265, 780)
    draw_rich_text(draw, desc_pos, desc, font_desc_reg, font_desc_bld, color_desc)

    # 3. Gambar Credential ID (Pill inside HTML is drawn around Y=220-260).
    cert_id_pos = (2170, 245)
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
