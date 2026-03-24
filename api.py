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

# --- CONFIG ---
BASE_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
BATCH          = "10"
ASSETS_DIR     = BASE_DIR / "assets"
TEMPLATE_COC   = ASSETS_DIR / "template_coc_blank.png"
TEMPLATE_COE   = ASSETS_DIR / "template_coe_blank.png"
TEMPLATE_REPORT= ASSETS_DIR / "template_report_blank.png"

FONT_PATH_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
FONT_PATH_REG  = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

try:
    font_name      = ImageFont.truetype(FONT_PATH_BOLD, 80)
    font_desc_reg  = ImageFont.truetype(FONT_PATH_REG, 38)
    font_desc_bld  = ImageFont.truetype(FONT_PATH_BOLD, 38)
    font_cert_id   = ImageFont.truetype(FONT_PATH_BOLD, 32)
    
    # Report Fonts
    font_rpt_name  = ImageFont.truetype(FONT_PATH_BOLD, 28)
    font_rpt_val   = ImageFont.truetype(FONT_PATH_BOLD, 22)
    font_rpt_score = ImageFont.truetype(FONT_PATH_BOLD, 48)
    font_rpt_grade = ImageFont.truetype(FONT_PATH_BOLD, 42)
    font_rpt_small = ImageFont.truetype(FONT_PATH_BOLD, 18)
    font_rpt_reg   = ImageFont.truetype(FONT_PATH_REG, 18)
except Exception:
    font_name = font_desc_reg = font_desc_bld = font_cert_id = ImageFont.load_default()
    font_rpt_name = font_rpt_val = font_rpt_score = font_rpt_grade = font_rpt_small = font_rpt_reg = ImageFont.load_default()

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

def pct_to_float(val):
    if not val: return 0.0
    s = str(val).replace('%', '').strip()
    try: return float(s)
    except: return 0.0

def safe_float(val):
    try: return float(val)
    except: return 0.0

# --- APP ---
app = FastAPI(title="REA Certificate API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CertRequest(BaseModel):
    name: str
    student_id: str
    atc_accum: Union[str, float, int] = "0%"
    current_score: Union[str, float, int] = 0
    current_grade: str = ""
    batch: str = BATCH
    cert_type: Optional[str] = None

class ReportRequest(BaseModel):
    name: str
    student_id: Union[str, int]
    batch: Union[str, int] = BATCH
    current_score: Union[str, int, float] = "0"
    current_grade: Union[str, int, float] = ""
    current_status: str = ""
    atc_accum: Union[str, int, float] = "0%"
    pre_test: Union[str, int, float] = ""
    post_test: Union[str, int, float] = ""
    fp: Union[str, int, float] = ""
    atr1: Union[str, int, float] = ""; prj1: Union[str, int, float] = ""
    atr2: Union[str, int, float] = ""; prj2: Union[str, int, float] = ""
    atr3: Union[str, int, float] = ""; prj3: Union[str, int, float] = ""
    atr4: Union[str, int, float] = ""; prj4: Union[str, int, float] = ""
    atr5: Union[str, int, float] = ""
    atr6: Union[str, int, float] = ""
    atr7: Union[str, int, float] = ""

def make_cert_id(batch: str) -> str:
    chars = string.ascii_uppercase + string.digits
    return f"REAENG{batch}" + ''.join(random.choices(chars, k=5))

def draw_cert_image(cert_type_label, name, cert_id, atc_str, score, grade):
    try:
        f_atc = float(str(atc_str).replace('%',''))
        if 0 < f_atc <= 1.0: atc_str = f"{int(round(f_atc * 100))}%"
    except: pass

    if cert_type_label == "BEST":
        img_p, desc = TEMPLATE_COE, f"For demonstrating exceptional dedication, fulfilling all comprehensive curriculum requirements, and successfully delivering an outstanding final project, thereby earning the status of <b>BEST STUDENT</b> in the following program:"
    elif cert_type_label == "COE":
        img_p, desc = TEMPLATE_COE, f"For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements with a score of <b>{int(score)}</b>, thereby earning the grade of <b>{grade}</b> in the following program:"
    else:
        img_p, desc = TEMPLATE_COC, f"For demonstrating strong commitment and successfully fulfilling the attendance requirements with an accumulation score of <b>{atc_str}</b> throughout the sessions, thereby earning the status of <b>PASSED</b> in the following program:"

    img = Image.open(img_p).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.text((260, 620), name, font=font_name, fill="#1e293b")
    draw_rich_text(draw, (265, 780), desc, font_desc_reg, font_desc_bld, "#334155")
    draw.text((2170, 245), cert_id, font=font_cert_id, fill="#0284c7", anchor="ra")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()

def draw_report_image(req: ReportRequest) -> bytes:
    img = Image.open(TEMPLATE_REPORT).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    navy, blue, muted = "#0C1526", "#2563EB", "#94A3B8"

    # Header Info
    draw.text((68, 178),  str(req.name),          font=font_rpt_name,  fill=navy, anchor="lm")
    draw.text((411, 176), str(req.student_id),   font=font_rpt_val,   fill=navy, anchor="mm")
    draw.text((68, 205),  f"Batch {req.batch}",   font=font_rpt_reg,   fill=muted, anchor="lm")
    
    # Score & Grade
    draw.text((564, 188), str(req.current_score), font=font_rpt_score, fill=blue, anchor="mm")
    draw.text((717, 186), str(req.current_grade), font=font_rpt_grade, fill=navy, anchor="mm")
    
    # Status Badge
    status_str = str(req.current_status).upper()
    status_colors = {
        "PASSED": ("#DCFCE7", "#166534"), "REMEDIAL": ("#FFEDD5", "#C2410C"),
        "NEED IMPROVEMENT": ("#FEF9C3", "#854D0E"), "FAILED": ("#FEE2E2", "#991B1B"),
    }
    bg_h, fg_h = status_colors.get(status_str, ("#E0F2FE", "#0369A1"))
    pill_x, pill_y, pill_h = 68, 291, 24
    bbox = draw.textbbox((0, 0), status_str, font=font_rpt_small)
    pill_w = bbox[2] - bbox[0] + 20
    draw.rounded_rectangle([pill_x - 10, pill_y - 12, pill_x + pill_w - 10, pill_y + 12], radius=6, fill=bg_h)
    draw.text((pill_x, pill_y), status_str, font=font_rpt_small, fill=fg_h, anchor="mm")

    def fv(v):
        s = str(v).strip()
        if not s or s in ('', '-1', '-', '—'): return '—'
        try:
            fl = float(s)
            return str(int(fl)) if fl == int(fl) else s
        except: return s

    # Attendance & Projects
    y_s = [436, 470, 504, 538, 572, 606, 639]
    courses = [
        (str(req.atr1), fv(req.prj1)), (str(req.atr2), fv(req.prj2)), (str(req.atr3), fv(req.prj3)),
        (str(req.atr4), fv(req.prj4)), (str(req.atr5), '—'), (str(req.atr6), '—'), (str(req.atr7), '—')
    ]
    for (atr, prj), cy in zip(courses, y_s):
        draw.text((529, cy), atr, font=font_rpt_reg, fill=navy, anchor="mm")
        draw.text((706, cy), prj, font=font_rpt_reg, fill=muted if prj == '—' else navy, anchor="mm")

    # Score Recap
    for cy, val in zip([770, 804, 838, 872], [fv(req.pre_test), fv(req.post_test), str(req.atc_accum), fv(req.fp)]):
        draw.text((359, cy), val, font=font_rpt_reg, fill=muted if val == '—' else navy, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()

@app.get("/health")
def health(): return {"status": "ok", "mode": "Pillow (PNG)"}

@app.post("/generate_cert")
def generate_cert(req: CertRequest, format: Optional[str] = None):
    atc_val, score_val = pct_to_float(req.atc_accum), safe_float(req.current_score)
    cert_type = (req.cert_type or "").upper()
    if cert_type not in ("COC", "COE", "BEST"):
        if score_val >= 70: cert_type = "COE"
        elif atc_val >= 70: cert_type = "COC"
        else: raise HTTPException(status_code=400, detail="Syarat tidak terpenuhi")
    
    cert_id = make_cert_id(req.batch)
    png_bytes = draw_cert_image(cert_type, req.name, cert_id, req.atc_accum, score_val, req.current_grade)
    filename = f"{req.name.replace(' ', '_')}_{cert_type}.png"
    if format == "json":
        import base64
        return {"status": "success", "filename": filename, "cert_id": cert_id, "base64": base64.b64encode(png_bytes).decode("utf-8")}
    return Response(content=png_bytes, media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

@app.post("/generate_report")
def generate_report(req: ReportRequest, format: Optional[str] = None):
    png_bytes = draw_report_image(req)
    filename = f"{req.name.replace(' ', '_')}_Report.png"
    if format == "json":
        import base64
        return {"status": "success", "filename": filename, "base64": base64.b64encode(png_bytes).decode("utf-8")}
    return Response(content=png_bytes, media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

