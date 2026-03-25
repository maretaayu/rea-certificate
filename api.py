"""
REA AI Engineering Certificate & Student Report API
==========================================
Native Pillow Implementation for 100% stable layouts on Vercel.
"""

import os, io, random, string, textwrap
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

FONT_PATH_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
FONT_PATH_REG  = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

try:
    font_name      = ImageFont.truetype(FONT_PATH_BOLD, 80)
    font_desc_reg  = ImageFont.truetype(FONT_PATH_REG, 38)
    font_desc_bld  = ImageFont.truetype(FONT_PATH_BOLD, 38)
    font_cert_id   = ImageFont.truetype(FONT_PATH_BOLD, 32)
    
    # Fonts for Report
    F_H1           = ImageFont.truetype(FONT_PATH_BOLD, 42)
    F_VAL          = ImageFont.truetype(FONT_PATH_BOLD, 20)
    F_LBL          = ImageFont.truetype(FONT_PATH_BOLD, 14)
    F_BODY         = ImageFont.truetype(FONT_PATH_REG,  16)
    F_B_B          = ImageFont.truetype(FONT_PATH_BOLD, 16)
except Exception:
    font_name = font_desc_reg = font_desc_bld = font_cert_id = F_H1 = F_VAL = F_LBL = F_BODY = F_B_B = ImageFont.load_default()

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
    description = "Generate PNG certificates and reports for AI Engineering Bootcamp via PIL (Vercel Serverless)",
    version     = "4.1.0",
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

class ReportRequest(BaseModel):
    name: str; student_id: str; batch: str = BATCH
    current_score: Union[str, float] = 0; current_grade: str = ""; current_status: str = ""
    atc_accum: Union[str, float] = "0%"; pre_test: str = "—"; post_test: str = "—"; fp: str = "—"
    atr1: str = "—"; prj1: str = "—"; atr2: str = "—"; prj2: str = "—"; atr3: str = "—"; prj3: str = "—"
    atr4: str = "—"; prj4: str = "—"; atr5: str = "—"; atr6: str = "—"; atr7: str = "—"

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def pct_to_float(val: Union[str, int, float]) -> float:
    s = str(val).strip()
    if s.endswith('%'):
        try: return float(s[:-1])
        except ValueError: return 0.0
    try:
        f = float(s)
        if 0 < f <= 1.0:
            return f * 100
        return f
    except ValueError:
        return 0.0

def safe_float(val: Union[str, int, float]) -> float:
    try:
        return float(str(val))
    except ValueError:
        return 0.0

def make_cert_id(batch: Union[str, int]) -> str:
    chars = string.ascii_uppercase + string.digits
    return f"REAENG{str(batch)}" + ''.join(random.choices(chars, k=5))

def draw_cert_image(
    cert_type_label: str,
    name: str,
    cert_id: str,
    atc_val_input: Union[str, int, float],
    score: float,
    grade: Union[str, int, float]
) -> bytes:
    
    atc_str = str(atc_val_input)
    grade_str = str(grade)
    try:
        f_atc = float(atc_str.replace('%', ''))
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
            f"with a score of <b>{int(score)}</b>, thereby earning the status of <b>PASSED</b> with the grade of <b>{grade_str}</b> in the following program:"
        )
    else:  # COC
        img_path = TEMPLATE_COC
        desc = (
            f"For actively participating and demonstrating commitment by fulfilling the cumulative attendance "
            f"requirement of <b>{atc_str}</b> throughout the sessions of the following program:"
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

    # 3. Gambar Credential ID
    cert_id_pos = (2170, 245)
    draw.text(cert_id_pos, cert_id, font=font_cert_id, fill=color_cert, anchor="ra")

    # 4. Patch "Verify Authenticity" URL (Since it's in the template)
    # Drawing a white box over the old URL and writing the new one.
    # Estimated position for the small footer area (X=260, Y=2330-2450)
    # 1835 was too high, footer is near the bottom.
    draw.rectangle([250, 2320, 1000, 2430], fill="#FFFFFF")
    draw.text((260, 2335), "Verify authenticity at ruangguru.com/rea/verify", font=get_font_report(FONT_PATH_REG, 22), fill="#64748b")

    # Export ke Bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()

def draw_report_v4(req: ReportRequest) -> bytes:
    W, H = 842, 1191 # A4 @ 72 DPI-ish
    img = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Header: Deep Navy
    draw.rectangle([0, 0, W, 180], fill="#0A192F")
    draw.text((50, 60),  "Student Report", font=F_H1, fill="#FFFFFF")
    draw.text((50, 110), f"AI ENGINEERING BOOTCAMP • BATCH {req.batch}", font=get_font_report(FONT_PATH_BOLD, 14), fill="#3B82F6")
    
    # Content Section
    y = 220
    def box(x, label, val, w):
        draw.rectangle([x, y, x+w, y+100], outline="#E5E7EB", width=2)
        draw.text((x+15, y+15), label.upper(), font=F_LBL, fill="#9CA3AF")
        draw.text((x+15, y+45), str(val), font=F_VAL, fill="#111827")

    box(50,  "Student Name", req.name, 350)
    # Subtitle for name box
    draw.text((50+15, y+75), f"Batch {req.batch} · AI Engineering Bootcamp", font=get_font_report(FONT_PATH_REG, 11), fill="#6B7280")
    
    box(410, "Student ID", req.student_id, 150)
    box(570, "Score", str(req.current_score), 100)
    box(680, "Grade", req.current_grade, 100)
    
    # Badge
    st = str(req.current_status).upper()
    bc = {"PASSED": ("#DCFCE7","#166534"), "FAILED": ("#FEE2E2","#991B1B")}.get(st, ("#F3F4F6","#374151"))
    draw.rounded_rectangle([50, 330, 200, 360], radius=5, fill=bc[0])
    draw.text((125, 345), st, font=get_font_report(FONT_PATH_BOLD, 12), fill=bc[1], anchor="mm")

    # Table: Attendance 
    ty = 400
    draw.rectangle([50, ty, W-50, ty+40], fill="#F9FAFB")
    draw.line([(50, ty), (50, ty+40)], fill="#3B82F6", width=5)
    draw.text((65, ty+10), "ATTENDANCE & PROJECT RECAP", font=get_font_report(FONT_PATH_BOLD, 18), fill="#111827")
    
    hy = ty + 50
    draw.text((65, hy), "COURSE MODULE", font=F_LBL, fill="#6B7280")
    draw.text((W-300, hy), "ATTENDANCE", font=F_LBL, fill="#6B7280")
    draw.text((W-150, hy), "SCORE", font=F_LBL, fill="#6B7280")
    
    ry = hy + 30
    def fv(v): s=str(v).strip(); return "—" if not s or s in ("","-1","-","—") else s
    rows = [
        ("Course 1 - Python", "1", fv(req.prj1)), ("Course 2 - Vibe Coding", "1", fv(req.prj2)),
        ("Course 3 - Machine Learning", "1", fv(req.prj3)), ("Course 4 - Deep Learning", "1", fv(req.prj4)),
        ("Course 5 - Visual Model", "1", "—"), ("Course 6 - Large Language Model", "1", "—"),
        ("Course 7 - Agentic AI", "1", "—")
    ]
    for m, a, p in rows:
        draw.text((65, ry), m, font=F_BODY, fill="#374151")
        draw.text((W-250, ry), a, font=F_B_B, fill="#111827", anchor="mm")
        draw.text((W-120, ry), p, font=F_B_B, fill="#111827", anchor="mm")
        ry += 40

    # Score Recap
    sy = ry + 20
    draw.rectangle([50, sy, W-50, sy+40], fill="#F9FAFB")
    draw.text((65, sy+10), "SCORE RECAP", font=get_font_report(FONT_PATH_BOLD, 18), fill="#111827")
    sy += 50
    recap = [("Pre Test", req.pre_test), ("Post Test", req.post_test), ("Attendance", req.atc_accum), ("Capstone", req.fp)]
    for lbl, val in recap:
        draw.text((65, sy), lbl, font=F_BODY, fill="#374151")
        draw.text((W-120, sy), fv(val), font=F_B_B, fill="#000000", anchor="mm")
        sy += 35

    buf = io.BytesIO(); img.save(buf, format="PNG", quality=95); buf.seek(0)
    return buf.read()

def get_font_report(path, size):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

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
            raise HTTPException(status_code=400, detail="Student tidak memenuhi syarat: score < 70 dan atc < 70%")

    if cert_type == "COE" and score_val < 70:
        raise HTTPException(status_code=400, detail="COE requires Current Score >= 70")
    if cert_type == "COC" and atc_val < 70:
        raise HTTPException(status_code=400, detail="COC requires Atc (Accum) >= 70%")

    cert_id  = make_cert_id(req.batch)
    png_bytes = draw_cert_image(
        cert_type_label = cert_type,
        name            = req.name,
        cert_id         = cert_id,
        atc_val_input   = req.atc_accum,
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

@app.post("/generate_report")
def generate_report(req: ReportRequest):
    return Response(content=draw_report_v4(req), media_type="image/png")
