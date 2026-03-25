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

    # Export ke Bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()

def truncate_text(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    # Keep removing characters until it fits with '...'
    while len(text) > 0 and draw.textlength(text + "...", font=font) > max_w:
        text = text[:-1]
    return text + "..."

def draw_report_v4(req: ReportRequest) -> bytes:
    W, H = 850, 1150 # Closest to the HTML container
    img = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Fonts
    F_H1 = get_font_report(FONT_PATH_BOLD, 36)
    F_SUB = get_font_report(FONT_PATH_BOLD, 12)
    F_LABEL = get_font_report(FONT_PATH_BOLD, 10)
    F_VAL_NAME = get_font_report(FONT_PATH_BOLD, 20)
    F_VAL_ID = get_font_report(FONT_PATH_BOLD, 14)
    F_VAL_BIG = get_font_report(FONT_PATH_BOLD, 36)
    F_SEC_TITLE = get_font_report(FONT_PATH_BOLD, 15)
    F_TH = get_font_report(FONT_PATH_BOLD, 10)
    F_TD = get_font_report(FONT_PATH_REG, 15)
    F_TD_B = get_font_report(FONT_PATH_BOLD, 15)
    
    # Header
    # Elegant Gradient
    for y in range(130):
        t = y / 130
        r = int(10 * (1-t) + 6 * t)
        g = int(25 * (1-t) + 49 * t)
        b = int(47 * (1-t) + 109 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    draw.text((48, 40), "Student Report", font=F_H1, fill="#FFFFFF")
    draw.text((48, 88), f"AI ENGINEERING BOOTCAMP • BATCH {req.batch}", font=F_SUB, fill="#60A5FA")

    # Logos overlay
    try:
        l_rea = Image.open('assets/Logo REA (black).png').convert("RGBA")
        w_rea = Image.new('L', l_rea.size, 255)
        l_rea_w = Image.merge('RGBA', (w_rea, w_rea, w_rea, l_rea.split()[3]))
        l_rea_w.thumbnail((120, 36), Image.Resampling.LANCZOS)
        
        l_sa = Image.open('assets/Logo SA Pro (black).png').convert("RGBA")
        w_sa = Image.new('L', l_sa.size, 255)
        l_sa_w = Image.merge('RGBA', (w_sa, w_sa, w_sa, l_sa.split()[3]))
        l_sa_w.thumbnail((120, 36), Image.Resampling.LANCZOS)

        # Paste SA rightmost
        sa_y = 65 - l_sa_w.height // 2
        sa_x = W - 48 - l_sa_w.width
        img.paste(l_sa_w, (sa_x, sa_y), l_sa_w)

        # Paste Sep
        sep_x = sa_x - 16
        draw.line([(sep_x, sa_y + 4), (sep_x, sa_y + l_sa_w.height - 4)], fill="#FFFFFF", width=1)

        # Paste REA
        rea_x = sep_x - 16 - l_rea_w.width
        rea_y = 65 - l_rea_w.height // 2
        img.paste(l_rea_w, (rea_x, rea_y), l_rea_w)
    except Exception as e:
        print(f"Failed to load logos: {e}")
    
    # Grid/Margins
    margin_x = 48
    y_info = 170
    info_h = 105
    w_info = W - 2 * margin_x
    
    # Helper to format float to int if no decimal
    def fmt_sc(val):
        try:
            f = float(val)
            return str(int(f)) if f.is_integer() else str(f)
        except:
            return str(val)

    # --- 2. 2-ROW INFO BOX ---
    h_row1 = 90
    h_row2 = 90
    h_total = h_row1 + h_row2

    draw.rectangle([margin_x, y_info, margin_x+w_info, y_info+h_total], outline="#E2E8F0", width=2, fill="#FFFFFF")

    y_row2 = y_info + h_row1
    draw.line([(margin_x, y_row2), (margin_x + w_info, y_row2)], fill="#E2E8F0", width=1)

    # ROW 1: Name and ID
    col1_w = int(w_info * 0.65) # ~490
    draw.line([(margin_x + col1_w, y_info), (margin_x + col1_w, y_row2)], fill="#E2E8F0", width=1)

    draw.text((margin_x + 20, y_info + 16), "STUDENT NAME", font=F_LABEL, fill="#94A3B8")
    name_text = truncate_text(draw, req.name, F_VAL_NAME, col1_w - 40)
    draw.text((margin_x + 20, y_info + 36), name_text, font=F_VAL_NAME, fill="#0F172A")
    draw.text((margin_x + 20, y_info + 64), f"Batch {req.batch} · AI Engineering Bootcamp", font=get_font_report(FONT_PATH_REG, 11), fill="#94A3B8")

    draw.text((margin_x + col1_w + 20, y_info + 16), "STUDENT ID", font=F_LABEL, fill="#94A3B8")
    draw.text((margin_x + col1_w + 20, y_info + 40), req.student_id, font=F_VAL_ID, fill="#0F172A")

    # ROW 2: Score, Grade, Status
    col2_w = w_info // 3
    draw.line([(margin_x + col2_w, y_row2), (margin_x + col2_w, y_info + h_total)], fill="#E2E8F0", width=1)
    draw.line([(margin_x + 2*col2_w, y_row2), (margin_x + 2*col2_w, y_info + h_total)], fill="#E2E8F0", width=1)

    draw.text((margin_x + 20, y_row2 + 16), "SCORE", font=F_LABEL, fill="#94A3B8")
    draw.text((margin_x + 20, y_row2 + 40), fmt_sc(req.current_score), font=F_VAL_BIG, fill="#2563EB")

    draw.text((margin_x + col2_w + 20, y_row2 + 16), "GRADE", font=F_LABEL, fill="#94A3B8")
    draw.text((margin_x + col2_w + 20, y_row2 + 40), str(req.current_grade), font=F_VAL_BIG, fill="#0F172A")

    draw.text((margin_x + 2*col2_w + 20, y_row2 + 16), "STATUS", font=F_LABEL, fill="#94A3B8")
    st = str(req.current_status).upper()
    badge_colors = {
        "PASSED": ("#DCFCE7", "#166534"),
        "FAILED": ("#FEE2E2", "#991B1B"),
        "NEED IMPROVEMENT": ("#FEF9C3", "#854D0E"),
        "NEED ASSISTANCE": ("#FFEDD5", "#9A3412")
    }
    bg_c, fg_c = badge_colors.get(st, ("#F1F5F9", "#475569"))
    b_w = 130
    b_h = 28
    b_x = margin_x + 2*col2_w + 20
    b_y = y_row2 + 40
    draw.rounded_rectangle([b_x, b_y, b_x + b_w, b_y + b_h], radius=6, fill=bg_c)
    draw.text((b_x + b_w/2, b_y + b_h/2 - 1), st, font=get_font_report(FONT_PATH_BOLD, 10), fill=fg_c, anchor="mm")

    # Section 1: Attendance & Project Recap
    y_sec = y_info + h_total + 30
    draw.rectangle([margin_x, y_sec, W-margin_x, y_sec+36], fill="#F8FAFC")
    draw.rectangle([margin_x, y_sec, margin_x+4, y_sec+36], fill="#2563EB")
    draw.text((margin_x + 20, y_sec + 10), "ATTENDANCE & PROJECT RECAP", font=F_SEC_TITLE, fill="#0F172A")

    y_th = y_sec + 50
    draw.text((margin_x + 20, y_th), "COURSE MODULE", font=F_TH, fill="#64748B")
    draw.text((W - 200, y_th), "ATTENDANCE", font=F_TH, fill="#64748B", anchor="ma")
    draw.text((W - margin_x - 30, y_th), "SCORE", font=F_TH, fill="#64748B", anchor="ma")
    draw.line([(margin_x, y_th + 20), (W-margin_x, y_th + 20)], fill="#E2E8F0", width=1)

    ry = y_th + 36
    def fv(v): s=str(v).strip(); return "—" if not s or s in ("","-1","-","—") else s
    rows = [
        ("Course 1 - Python", "1", fv(req.prj1)), 
        ("Course 2 - Vibe Coding", "1", fv(req.prj2)),
        ("Course 3 - Machine Learning", "1", fv(req.prj3)), 
        ("Course 4 - Deep Learning", "1", fv(req.prj4)),
        ("Course 5 - Visual Model", "1", "—"), 
        ("Course 6 - Large Language Model", "1", "—"),
        ("Course 7 - Agentic AI", "1", "—")
    ]
    for m, a, p in rows:
        draw.text((margin_x + 20, ry), m, font=get_font_report(FONT_PATH_REG, 13), fill="#334155")
        draw.text((W - 200, ry+6), str(a), font=get_font_report(FONT_PATH_BOLD, 13), fill="#0F172A", anchor="mm")
        color_p = "#94A3B8" if p == "—" else "#0F172A"
        draw.text((W - margin_x - 30, ry+6), str(p), font=get_font_report(FONT_PATH_BOLD, 13), fill=color_p, anchor="mm")
        ry += 38

    # Section 2: Two Column Layout (Score Recap + Grading Scale)
    ry += 10
    col_w = (W - 2 * margin_x - 22) // 2 # 22px gap
    
    x_left = margin_x
    x_right = margin_x + col_w + 22

    # Titles
    draw.rectangle([x_left, ry, x_left + col_w, ry+36], fill="#F8FAFC")
    draw.rectangle([x_left, ry, x_left+4, ry+36], fill="#2563EB")
    draw.text((x_left + 20, ry+10), "SCORE RECAP", font=F_SEC_TITLE, fill="#0F172A")
    
    draw.rectangle([x_right, ry, x_right + col_w, ry+36], fill="#F8FAFC")
    draw.rectangle([x_right, ry, x_right+4, ry+36], fill="#2563EB")
    draw.text((x_right + 20, ry+10), "GRADING SCALE", font=F_SEC_TITLE, fill="#0F172A")

    # Table Heads
    y_th2 = ry + 50
    draw.text((x_left + 20, y_th2), "ASSESSMENT", font=F_TH, fill="#64748B")
    draw.text((x_left + col_w - 20, y_th2), "SCORE", font=F_TH, fill="#64748B", anchor="ma")
    draw.line([(x_left, y_th2+20), (x_left + col_w, y_th2+20)], fill="#E2E8F0", width=1)

    draw.text((x_right + 25, y_th2), "GRADE", font=F_TH, fill="#64748B", anchor="ma")
    draw.text((x_right + 65, y_th2), "RANGE", font=F_TH, fill="#64748B")
    draw.text((x_right + col_w - 55, y_th2), "STATUS", font=F_TH, fill="#64748B", anchor="ma")
    draw.line([(x_right, y_th2+20), (x_right + col_w, y_th2+20)], fill="#E2E8F0", width=1)
    
    # Helper to parse attendance percentage
    def fmt_atc(val):
        try:
            f = float(val)
            if f <= 1.0: return f"{int(round(f * 100))}%"
            if "%" not in str(val): return f"{f}%"
        except: pass
        return str(val)

    # Left Row (Score Recap)
    ry_left = y_th2 + 36
    recap = [("Pre Test Score", fv(req.pre_test)), ("Post Test Score", fv(req.post_test)), ("Cumulative Attendance Rate", fmt_atc(req.atc_accum)), ("Capstone Project", fv(req.fp))]
    for lbl, val in recap:
        draw.text((x_left + 20, ry_left), lbl, font=get_font_report(FONT_PATH_REG, 12), fill="#334155")
        color_val = "#94A3B8" if val == "—" else "#0F172A"
        draw.text((x_left + col_w - 20, ry_left+6), str(val), font=get_font_report(FONT_PATH_BOLD, 12), fill=color_val, anchor="mm")
        draw.line([(x_left, ry_left+24), (x_left + col_w, ry_left+24)], fill="#F1F5F9", width=1)
        ry_left += 34

    # Right Row (Grading Scale)
    ry_right = y_th2 + 36
    grades = [
        ("A", "85 - 100", "Passed", badge_colors["PASSED"]),
        ("B", "70 - 84.99", "Passed", badge_colors["PASSED"]),
        ("C", "60 - 69.99", "Need Improvement", badge_colors["NEED IMPROVEMENT"]),
        ("D", "45 - 59.99", "Need Assistance", badge_colors["NEED ASSISTANCE"]),
        ("E", "< 45", "Failed", badge_colors["FAILED"])
    ]
    for g, r, s_text, (bg, fg) in grades:
        # Tag
        draw.rounded_rectangle([x_right + 12, ry_right - 4, x_right + 38, ry_right + 18], radius=6, fill="#0F172A")
        draw.text((x_right + 25, ry_right + 7), g, font=get_font_report(FONT_PATH_BOLD, 12), fill="#FFFFFF", anchor="mm")
        
        # Range
        draw.text((x_right + 65, ry_right), r, font=get_font_report(FONT_PATH_REG, 11), fill="#64748B")
        
        # Status Label
        b_w = 100
        draw.rounded_rectangle([x_right + col_w - b_w - 5, ry_right - 4, x_right + col_w - 5, ry_right + 18], radius=5, fill=bg)
        draw.text((x_right + col_w - b_w/2 - 5, ry_right + 7), s_text, font=get_font_report(FONT_PATH_BOLD, 9), fill=fg, anchor="mm")
        
        draw.line([(x_right, ry_right+26), (x_right + col_w, ry_right+26)], fill="#F1F5F9", width=1)
        ry_right += 32

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
