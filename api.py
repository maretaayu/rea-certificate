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

def draw_report_v4(req: ReportRequest):
    # Polished formal design with elegant spacing, readable fonts, and dynamic data.
    FONT_PATH_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
    FONT_PATH_REG = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

    def get_font_report(path, size):
        try: return ImageFont.truetype(path, size)
        except: return ImageFont.load_default()

    # Create Canvas (Balanced height)
    W, H = 850, 1250
    img = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Fonts
    F_H1 = get_font_report(FONT_PATH_BOLD, 32)
    F_VAL = get_font_report(FONT_PATH_REG, 13)
    F_VAL_B = get_font_report(FONT_PATH_BOLD, 13)
    F_TH = get_font_report(FONT_PATH_BOLD, 13)
    F_GRADE = get_font_report(FONT_PATH_BOLD, 14)
    F_BADGE = get_font_report(FONT_PATH_BOLD, 11)
    F_TITLE = get_font_report(FONT_PATH_BOLD, 15)

    # Colors
    C_DARK = "#0F172A"
    C_LIGHT = "#F8FAFC"
    C_BORDER = "#E2E8F0"
    C_TEXT = "#475569"
    C_TEXT_BOLD = "#0F172A"

    # --- 1. HEADER ---
    header_h = 140
    draw.rectangle([0, 0, W, header_h], fill=C_DARK)
    draw.text((60, header_h//2), "STUDENT REPORT", font=F_H1, fill="#FFFFFF", anchor="lm")
    
    # Logos
    try:
        def prepare_logo(path, target_h):
            logo = Image.open(path).convert("RGBA")
            alpha = logo.split()[3]
            white = Image.new('RGB', logo.size, (255, 255, 255))
            white_logo = Image.merge('RGBA', (white.split()[0], white.split()[1], white.split()[2], alpha))
            ratio = target_h / float(logo.size[1])
            new_size = (int(float(logo.size[0]) * ratio), target_h)
            return white_logo.resize(new_size, Image.Resampling.LANCZOS)
        l_rea_w = prepare_logo('assets/Logo REA (black).png', 42)
        l_sa_w = prepare_logo('assets/Logo SA Pro (black).png', 42)
        sa_x = W - 60 - l_sa_w.width
        sa_y = header_h // 2 - l_sa_w.height // 2
        img.paste(l_sa_w, (sa_x, sa_y), l_sa_w)
        sep_x = sa_x - 18
        draw.line([(sep_x, sa_y + 4), (sep_x, sa_y + l_sa_w.height - 4)], fill="#FFFFFF", width=1)
        rea_x = sep_x - 18 - l_rea_w.width
        rea_y = header_h // 2 - l_rea_w.height // 2
        img.paste(l_rea_w, (rea_x, rea_y), l_rea_w)
    except Exception as e: print(f"Logo error: {e}")

    def draw_cell(draw, x, y, w, h, text, font, bg_color, text_color, align="center"):
        draw.rectangle([x, y, x+w, y+h], fill=bg_color, outline=C_BORDER, width=1)
        if align == "center":
            draw.text((x + w/2, y + h/2 - 1), str(text), font=font, fill=text_color, anchor="mm")
        elif align == "left":
            draw.text((x + 24, y + h/2 - 1), str(text), font=font, fill=text_color, anchor="lm")

    margin_x = 60
    w_main = W - 2 * margin_x

    # --- 2. TOP GRID (Dynamic Widths: 60/40) ---
    y_grid = header_h + 40
    r_h = 52
    w_left = int(w_main * 0.6)
    w_right = w_main - w_left
    
    l_lbl_w = int(w_left * 0.3)
    l_val_w = w_left - l_lbl_w
    r_lbl_w = int(w_right * 0.5)
    r_val_w = w_right - r_lbl_w

    def fv(v): s=str(v).strip(); return "-" if s in ("", "-1", "—", "None") or not s else s
    def fmt_sc(val):
        try:
            f = float(val)
            return str(int(f)) if f.is_integer() else str(f)
        except: return str(val)

    # Row 1
    draw_cell(draw, margin_x, y_grid, l_lbl_w, r_h, "Student Name", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+l_lbl_w, y_grid, l_val_w, r_h, req.name, F_VAL, "#FFFFFF", C_TEXT_BOLD, align="left")
    draw_cell(draw, margin_x+w_left, y_grid, r_lbl_w, r_h, "Current Score", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+w_left+r_lbl_w, y_grid, r_val_w, r_h, fmt_sc(req.current_score), F_VAL, "#FFFFFF", C_TEXT_BOLD)

    # Row 2
    y_grid += r_h
    draw_cell(draw, margin_x, y_grid, l_lbl_w, r_h, "Student ID", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+l_lbl_w, y_grid, l_val_w, r_h, req.student_id, F_VAL, "#FFFFFF", C_TEXT_BOLD, align="left")
    draw_cell(draw, margin_x+w_left, y_grid, r_lbl_w, r_h, "CCGPA", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+w_left+r_lbl_w, y_grid, r_val_w, r_h, fv(req.current_grade), F_VAL, "#FFFFFF", C_TEXT_BOLD)

    # Row 3
    y_grid += r_h
    draw_cell(draw, margin_x, y_grid, l_lbl_w, r_h, "Program", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+l_lbl_w, y_grid, l_val_w, r_h, "AI Engineering Bootcamp Batch 10", F_VAL, "#FFFFFF", C_TEXT_BOLD, align="left")
    draw_cell(draw, margin_x+w_left, y_grid, r_lbl_w, r_h, "Status", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+w_left+r_lbl_w, y_grid, r_val_w, r_h, str(req.current_status).title(), F_VAL, "#FFFFFF", C_TEXT_BOLD)

    # --- 3. ATTENDANCE & PROJECT RECAP (Full Width) ---
    y_sec2 = y_grid + r_h + 50 
    draw.text((margin_x, y_sec2), "Attendance & Project Recap", font=F_TITLE, fill=C_TEXT_BOLD)
    y_sec2 += 34 # Gap below title

    # Header Recap
    c1, c2, c3 = int(w_main*0.45), int(w_main*0.25), w_main - int(w_main*0.45) - int(w_main*0.25)
    draw_cell(draw, margin_x, y_sec2, c1, r_h, "Course Name", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, margin_x+c1, y_sec2, c2, r_h, "Attendance", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, margin_x+c1+c2, y_sec2, c3, r_h, "Project", F_TH, C_DARK, "#FFFFFF")
    y_sec2 += r_h

    def fmt_atc(val):
        try:
            f = float(str(val).replace('%',''))
            if 0 < f <= 1.0: return f"{int(round(f * 100))}%"
            if "%" not in str(val): return f"{int(f)}%"
        except: pass
        s = str(val).strip()
        if s in ["", "-", "—", "None"]: return "100%"
        return s

    rows = [
        ("Course 1 - Python", req.atr1, req.prj1), ("Course 2 - Vibe Coding & n8n", req.atr2, req.prj2),
        ("Course 3 - Machine Learning", req.atr3, req.prj3), ("Course 4 - Deep Learning", req.atr4, req.prj4),
        ("Course 5 - Visual Model & RAG", req.atr5, "-"), ("Course 6 - Large Language Model", req.atr6, "-"),
        ("Course 7 - Speech Model & Agentic AI", req.atr7, "-")
    ]
    for m, a, p in rows:
        draw_cell(draw, margin_x, y_sec2, c1, r_h, m, F_VAL_B, "#FFFFFF", C_TEXT_BOLD, align="center")
        draw_cell(draw, margin_x+c1, y_sec2, c2, r_h, fmt_atc(a), F_VAL, "#FFFFFF", C_TEXT)
        draw_cell(draw, margin_x+c1+c2, y_sec2, c3, r_h, fv(p), F_VAL, "#FFFFFF", C_TEXT)
        y_sec2 += r_h

    # --- 4. SCORE RECAP & GRADING SCALE ---
    y_sec3 = y_sec2 + 50
    draw.text((margin_x, y_sec3), "Score Recap & Grading Scale", font=F_TITLE, fill=C_TEXT_BOLD)
    y_sec3 += 34
    
    r_h_inner = 44 # Maintain 44 for inner tables
    gap = 20
    t_w = (w_main - gap) // 2
    x_L, x_R = margin_x, margin_x + t_w + gap

    # Score Recap
    s1, s2 = int(t_w * 0.6), t_w - int(t_w * 0.6)
    draw_cell(draw, x_L, y_sec3, s1, r_h_inner, "Score", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, x_L+s1, y_sec3, s2, r_h_inner, "Score", F_TH, C_DARK, "#FFFFFF")
    y_L = y_sec3 + r_h_inner
    recap = [("Pre Test Score", fv(req.pre_test)), ("Post Test Score", fv(req.post_test)), ("Cumulative Attendance Rate", fmt_atc(req.atc_accum)), ("Capstone Project", fv(req.fp))]
    for lbl, val in recap:
        draw_cell(draw, x_L, y_L, s1, r_h_inner, lbl, F_VAL_B, C_LIGHT, C_TEXT_BOLD, align="center")
        draw_cell(draw, x_L+s1, y_L, s2, r_h_inner, str(val), F_VAL, "#FFFFFF", C_TEXT)
        y_L += r_h_inner

    # Grading Scale
    draw_cell(draw, x_R, y_sec3, t_w, r_h_inner, "Grading Scale", F_TH, C_LIGHT, C_TEXT_BOLD)
    y_R = y_sec3 + r_h_inner
    badge_colors = {"PASSED": ("#DCFCE7", "#166534"), "FAILED": ("#FEE2E2", "#991B1B"), "NEED IMPROVEMENT": ("#FEF9C3", "#854D0E"), "NEED ASSISTANCE": ("#FFEDD5", "#9A3412")}
    grades = [("A", "85 - 100", "PASSED", badge_colors["PASSED"]), ("B", "70 - 84.99", "PASSED", badge_colors["PASSED"]), ("C", "60 - 69.99", "NEED IMPROVEMENT", badge_colors["NEED IMPROVEMENT"]), ("D", "45 - 59.99", "NEED ASSISTANCE", badge_colors["NEED ASSISTANCE"]), ("E", "< 45", "FAILED", badge_colors["FAILED"])]
    g1, g2, g3 = int(t_w * 0.15), int(t_w * 0.35), int(t_w * 0.5)
    for g, r, s, (bg, fg) in grades:
        draw_cell(draw, x_R, y_R, g1, r_h_inner, "", F_VAL, "#FFFFFF", C_TEXT)
        draw.rounded_rectangle([x_R+10, y_R+8, x_R+g1-10, y_R+r_h_inner-8], radius=4, fill=C_DARK)
        draw.text((x_R+g1/2, y_R+r_h_inner/2-1), g, font=F_GRADE, fill="#FFFFFF", anchor="mm")
        draw_cell(draw, x_R+g1, y_R, g2, r_h_inner, r, F_VAL, "#FFFFFF", C_TEXT)
        draw_cell(draw, x_R+g1+g2, y_R, g3, r_h_inner, "", F_VAL, "#FFFFFF", C_TEXT)
        draw.rounded_rectangle([x_R+g1+g2+10, y_R+8, x_R+g1+g2+g3-10, y_R+r_h_inner-8], radius=6, fill=bg)
        draw.text((x_R+g1+g2+g3/2, y_R+r_h_inner/2-1), s.title() if s != "PASSED" else "Passed", font=F_BADGE, fill=fg, anchor="mm")
        y_R += r_h_inner

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
