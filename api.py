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
    font_name    = ImageFont.truetype(FONT_PATH_BOLD, 80)
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
    
    # 1. Gambar Nama - ukuran fixed 80px untuk semua nama
    name_pos = (260, 620)
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

    # Auto-detect cert type if not explicitly provided
    if cert_type not in ("COC", "COE", "BEST"):
        if score_val >= 70:
            cert_type = "COE"   # Dapet COE (juga berhak COC, tapi perlu hit API terpisah)
        elif atc_val >= 70:
            cert_type = "COC"   # Hanya COC (attendance only)
        else:
            raise HTTPException(status_code=400, detail="Student tidak memenuhi syarat: score < 70 dan atc < 70%")

    # Validasi eksplisit per cert type
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

TEMPLATE_REPORT= ASSETS_DIR / "template_report_blank.png"

class ReportRequest(BaseModel):
    name          : str
    student_id    : Union[str, int]
    batch         : Union[str, int]        = BATCH
    current_score : Union[str, int, float] = "0"
    current_grade : Union[str, int, float] = ""
    current_status: str                    = ""
    atc_accum     : Union[str, int, float] = "0%"
    pre_test      : Union[str, int, float] = ""
    post_test     : Union[str, int, float] = ""
    fp            : Union[str, int, float] = ""
    atr1          : Union[str, int, float] = ""
    prj1          : Union[str, int, float] = ""
    atr2          : Union[str, int, float] = ""
    prj2          : Union[str, int, float] = ""
    atr3          : Union[str, int, float] = ""
    prj3          : Union[str, int, float] = ""
    atr4          : Union[str, int, float] = ""
    prj4          : Union[str, int, float] = ""
    atr5          : Union[str, int, float] = ""
    atr6          : Union[str, int, float] = ""
    atr7          : Union[str, int, float] = ""

# ─── REPORT IMAGE (Vercel Native Pillow) ──────────────────────────────────────
try:
    from PIL import ImageColor
    font_rpt_name  = ImageFont.truetype(FONT_PATH_BOLD, 28)
    font_rpt_val   = ImageFont.truetype(FONT_PATH_BOLD, 26)
    font_rpt_score = ImageFont.truetype(FONT_PATH_BOLD, 42)
    font_rpt_small = ImageFont.truetype(FONT_PATH_REG, 22)
except Exception:
    font_rpt_name = font_rpt_val = font_rpt_score = font_rpt_small = ImageFont.load_default()

def draw_report_image(req: ReportRequest) -> bytes:
    img  = Image.open(TEMPLATE_REPORT).convert("RGB")
    draw = ImageDraw.Draw(img)

    navy  = "#0A192F"
    blue  = "#0284C7"
    muted = "#94A3B8"

    # Row 1: Name, Student ID
    draw.text((510, 478), str(req.name),          font=font_rpt_name,  fill=navy, anchor="lm")
    draw.text((1478, 478), str(req.student_id),   font=font_rpt_val,   fill=navy, anchor="lm")
    # Row 2: Program, Current Score
    draw.text((510, 604),  f"AI Engineering Bootcamp Batch {req.batch}", font=font_rpt_small, fill=navy, anchor="lm")
    draw.text((1478, 614), str(req.current_score), font=font_rpt_score, fill=blue, anchor="lm")
    # Row 3: Grade
    draw.text((510, 748),  str(req.current_grade), font=font_rpt_name,  fill=navy, anchor="lm")
    
    status_str = str(req.current_status).upper()
    status_color_map = {
        "PASSED":           ("#DCFCE7", "#166534"),
        "REMEDIAL":         ("#FFEDD5", "#C2410C"),
        "NEED IMPROVEMENT": ("#FEF9C3", "#854D0E"),
        "FAILED":           ("#FEE2E2", "#991B1B"),
    }
    bg_hex, fg_hex = status_color_map.get(status_str, ("#E0F2FE", "#0369A1"))
    
    pill_x, pill_y, pill_h, pill_pad_x = 994, 734, 36, 20
    bbox = draw.textbbox((0, 0), status_str, font=font_rpt_small)
    pill_w = bbox[2] - bbox[0] + pill_pad_x * 2
    from PIL import ImageColor
    bg_rgb = ImageColor.getrgb(bg_hex)
    fg_rgb = ImageColor.getrgb(fg_hex)
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=pill_h // 2, fill=bg_rgb)
    draw.text((pill_x + pill_pad_x, pill_y + pill_h // 2), status_str, font=font_rpt_small, fill=fg_rgb, anchor="lm")

    # Attendance & Project
    atr_cx, prj_cx = 1384, 1737
    def fv(v): 
        s = str(v).strip()
        if not s or s in ('', '-1', '-', '—'): return '—'
        try:
            fl = float(s)
            return '—' if fl < 0 else (str(int(fl)) if fl == int(fl) else s)
        except: return s

    courses = [
        (str(req.atr1), fv(req.prj1)), (str(req.atr2), fv(req.prj2)), (str(req.atr3), fv(req.prj3)),
        (str(req.atr4), fv(req.prj4)), (str(req.atr5), '—'), (str(req.atr6), '—'), (str(req.atr7), '—'),
    ]
    for (atr, prj), cy in zip(courses, [1052, 1126, 1200, 1274, 1348, 1422, 1496]):
        draw.text((atr_cx, cy), atr, font=font_rpt_small, fill=navy, anchor="mm")
        draw.text((prj_cx, cy), prj, font=font_rpt_small, fill=muted if prj == '—' else navy, anchor="mm")

    # Score Recap
    score_cx = 1083
    for cy, val in [(1763, fv(req.pre_test)), (1827, fv(req.post_test)), (1891, str(req.atc_accum)), (1954, fv(req.fp))]:
        draw.text((score_cx, cy), val, font=font_rpt_small, fill=muted if val == "—" else navy, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()


@app.post("/generate_report")
def generate_report(req: ReportRequest, format: Optional[str] = None):
    try:
        png_bytes = draw_report_image(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    filename  = f"{str(req.name).replace(' ', '_')}_Report.png"

    if format == "json":
        import base64
        return {
            "status"  : "success",
            "filename": filename,
            "base64"  : base64.b64encode(png_bytes).decode("utf-8"),
        }

    return Response(
        content    = png_bytes,
        media_type = "image/png",
        headers    = {"Content-Disposition": f'attachment; filename="{filename}"'},
    )
