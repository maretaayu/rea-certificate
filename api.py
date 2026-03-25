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
    # This report mimics the rigid PDF formal design (dark blue tables, light blue accents, white cells).
    FONT_PATH_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
    FONT_PATH_REG = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

    def get_font_report(path, size):
        try: return ImageFont.truetype(path, size)
        except: return ImageFont.load_default()

    # Create Canvas
    W, H = 850, 1150
    img = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)

    # Fonts
    F_H1 = get_font_report(FONT_PATH_BOLD, 28)
    F_VAL = get_font_report(FONT_PATH_REG, 13)
    F_VAL_B = get_font_report(FONT_PATH_BOLD, 13)
    F_TH = get_font_report(FONT_PATH_BOLD, 12)
    F_TD = get_font_report(FONT_PATH_BOLD, 12)
    F_GRADE = get_font_report(FONT_PATH_BOLD, 12)
    F_BADGE = get_font_report(FONT_PATH_BOLD, 10)

    # Colors
    C_DARK = "#29385C" # Dark navy for top bar and headers
    C_LIGHT = "#EAF3FC" # Light blue for field keys
    C_BORDER = "#D6E0EF" # Subtle borders
    C_TEXT = "#1E293B"

    # --- 1. HEADER ---
    header_h = 100
    draw.rectangle([0, 0, W, header_h], fill=C_DARK)
    draw.text((48, header_h//2), "STUDENT REPORT", font=F_H1, fill="#FFFFFF", anchor="lm")
    
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

        sa_y = header_h // 2 - l_sa_w.height // 2
        sa_x = W - 48 - l_sa_w.width
        img.paste(l_sa_w, (sa_x, sa_y), l_sa_w)

        sep_x = sa_x - 16
        draw.line([(sep_x, sa_y + 4), (sep_x, sa_y + l_sa_w.height - 4)], fill="#FFFFFF", width=1)

        rea_x = sep_x - 16 - l_rea_w.width
        rea_y = header_h // 2 - l_rea_w.height // 2
        img.paste(l_rea_w, (rea_x, rea_y), l_rea_w)
    except Exception as e:
        print(f"Failed to load logos: {e}")

    # Helper for drawing table cells
    def draw_cell(draw, x, y, w, h, text, font, bg_color, text_color, align="center"):
        draw.rectangle([x, y, x+w, y+h], fill=bg_color, outline=C_BORDER, width=1)
        if align == "center":
            draw.text((x + w/2, y + h/2 - 1), str(text), font=font, fill=text_color, anchor="mm")
        elif align == "left":
            draw.text((x + 16, y + h/2 - 1), str(text), font=font, fill=text_color, anchor="lm")

    margin_x = 48
    w_main = W - 2 * margin_x

    # --- 2. TOP GRID (3 rows) ---
    y_grid = header_h + 30
    r_h = 40
    c1_w, c2_w, c3_w, c4_w = int(w_main*0.22), int(w_main*0.42), int(w_main*0.18), int(w_main*0.18)

    # Helper format values
    def fmt_sc(val):
        try:
            f = float(val)
            return str(int(f)) if f.is_integer() else str(f)
        except: return str(val)

    # Row 1
    draw_cell(draw, margin_x, y_grid, c1_w, r_h, "Student Name", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+c1_w, y_grid, c2_w, r_h, req.name, F_VAL, "#FFFFFF", C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w, y_grid, c3_w, r_h, "Current Score", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w+c3_w, y_grid, c4_w, r_h, "CCGPA", F_TH, C_LIGHT, C_TEXT)

    # Row 2
    y_grid += r_h
    draw_cell(draw, margin_x, y_grid, c1_w, r_h, "Student ID", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+c1_w, y_grid, c2_w, r_h, req.student_id, F_VAL, "#FFFFFF", C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w, y_grid, c3_w, r_h, fmt_sc(req.current_score), F_VAL, "#FFFFFF", C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w+c3_w, y_grid, c4_w, r_h, str(req.current_grade), F_VAL, "#FFFFFF", C_TEXT)

    # Row 3
    y_grid += r_h
    draw_cell(draw, margin_x, y_grid, c1_w, r_h, "Program", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+c1_w, y_grid, c2_w, r_h, f"AI Engineering Bootcamp Batch {req.batch}", F_VAL, "#FFFFFF", C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w, y_grid, c3_w, r_h, "Status", F_TH, C_LIGHT, C_TEXT)
    draw_cell(draw, margin_x+c1_w+c2_w+c3_w, y_grid, c4_w, r_h, str(req.current_status).title() if str(req.current_status).lower() != "passed" else "Passed", F_VAL, "#FFFFFF", C_TEXT)

    # --- 3. ATTENDANCE & PROJECT RECAP ---
    y_sec2 = y_grid + 30
    r_h = 36
    draw_cell(draw, margin_x, y_sec2, w_main, r_h, "Attendance & Project Recap", F_TH, C_DARK, "#FFFFFF")
    y_sec2 += r_h

    # Inner table padding
    t_margin = margin_x + 80
    t_w = W - 2 * t_margin
    t2_c1, t2_c2, t2_c3 = int(t_w*0.5), int(t_w*0.25), t_w - int(t_w*0.5) - int(t_w*0.25)

    draw_cell(draw, t_margin, y_sec2, t2_c1, r_h, "Course Name", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, t_margin+t2_c1, y_sec2, t2_c2, r_h, "Attendance", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, t_margin+t2_c1+t2_c2, y_sec2, t2_c3, r_h, "Project", F_TH, C_DARK, "#FFFFFF")
    y_sec2 += r_h

    def fmt_atc(val):
        try:
            f = float(val)
            if f <= 1.0: return f"{int(round(f * 100))}%"
            if "%" not in str(val): return f"{f}%"
        except: pass
        if str(val).strip() in ["", "-"]: return "100%"
        return str(val).strip()

    def fv(v): s=str(v).strip(); return "-" if not s or s in ("","-1","—") else s

    rows = [
        ("Course 1 - Python", "1", fv(req.prj1)), 
        ("Course 2 - Vibe Coding & n8n", "1", fv(req.prj2)),
        ("Course 3 - Machine Learning", "0.5", fv(req.prj3)), 
        ("Course 4 - Deep Learning", "0.5", fv(req.prj4)),
        ("Course 5 - Visual Model & RAG", "1", "-"), 
        ("Course 6 - Large Language Model", "1", "-"),
        ("Course 7 - Speech Model & Agentic AI", "1", "-")
    ]
    for m, a, p in rows:
        draw_cell(draw, t_margin, y_sec2, t2_c1, r_h, m, F_TD, "#FFFFFF", C_TEXT, align="center")
        draw_cell(draw, t_margin+t2_c1, y_sec2, t2_c2, r_h, fmt_atc(a), F_VAL, "#FFFFFF", C_TEXT)
        draw_cell(draw, t_margin+t2_c1+t2_c2, y_sec2, t2_c3, r_h, fv(p), F_VAL, "#FFFFFF", C_TEXT)
        y_sec2 += r_h

    # --- 4. SCORE RECAP & GRADING SCALE ---
    y_sec3 = y_sec2 + 30
    draw_cell(draw, margin_x, y_sec3, w_main, r_h, "Score Recap & Grading Scale", F_TH, C_DARK, "#FFFFFF")
    y_sec3 += r_h

    # Two side-by-side tables with a fixed gap
    gap = 20
    t_w3 = (w_main - gap) // 2
    x_left = margin_x
    x_right = margin_x + t_w3 + gap

    # Left Table: Score Recap
    draw_cell(draw, x_left, y_sec3, t_w3//2, r_h, "Score", F_TH, C_DARK, "#FFFFFF")
    draw_cell(draw, x_left+t_w3//2, y_sec3, t_w3 - t_w3//2, r_h, "Score", F_TH, C_DARK, "#FFFFFF")
    y_left = y_sec3 + r_h

    recap_rows = [
        ("Pre Test Score", fv(req.pre_test)),
        ("Post Test Score", fv(req.post_test)),
        ("Cummulative Attendance Rate", fmt_atc(req.atc_accum)),
        ("Capstone Project", fv(req.fp)),
    ]
    for lbl, val in recap_rows:
        draw_cell(draw, x_left, y_left, t_w3//2, r_h, lbl, F_TD, C_LIGHT, C_TEXT, align="center")
        draw_cell(draw, x_left+t_w3//2, y_left, t_w3 - t_w3//2, r_h, str(val), F_VAL, "#FFFFFF", C_TEXT)
        y_left += r_h

    # Right Table: Grading Scale
    draw_cell(draw, x_right, y_sec3, t_w3, r_h, "Grading Scale", F_TH, C_LIGHT, C_TEXT)
    y_right = y_sec3 + r_h

    badge_colors = {
        "PASSED": ("#DCFCE7", "#166534"),
        "FAILED": ("#FEE2E2", "#991B1B"),
        "NEED IMPROVEMENT": ("#FEF9C3", "#854D0E"),
        "NEED ASSISTANCE": ("#FFEDD5", "#9A3412")
    }
    grades = [
        ("A", "85 - 100", "PASSED", badge_colors["PASSED"]),
        ("B", "70 - 84.99", "PASSED", badge_colors["PASSED"]),
        ("C", "60 - 69.99", "NEED IMPROVEMENT", badge_colors["NEED IMPROVEMENT"]),
        ("D", "45 - 59.99", "NEED ASSISTANCE", badge_colors["NEED ASSISTANCE"]),
        ("E", "< 45", "FAILED", badge_colors["FAILED"])
    ]
    g_c1, g_c2, g_c3 = int(t_w3 * 0.15), int(t_w3 * 0.35), int(t_w3 * 0.5)
    for g, r, s_text, (bg, fg) in grades:
        # Col 1: Grade Block
        draw_cell(draw, x_right, y_right, g_c1, r_h, "", F_VAL, "#FFFFFF", C_TEXT)
        bx, by, bw, bh = x_right + 8, y_right + 6, g_c1 - 16, r_h - 12
        draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=4, fill=C_DARK)
        draw.text((x_right + g_c1/2, y_right + r_h/2 - 1), g, font=F_GRADE, fill="#FFFFFF", anchor="mm")
        
        # Col 2: Range
        draw_cell(draw, x_right+g_c1, y_right, g_c2, r_h, r, F_VAL, "#FFFFFF", C_TEXT)
        
        # Col 3: Status
        draw_cell(draw, x_right+g_c1+g_c2, y_right, g_c3, r_h, "", F_VAL, "#FFFFFF", C_TEXT)
        st_bx, st_by, st_bw, st_bh = x_right+g_c1+g_c2 + 10, y_right + 6, g_c3 - 20, r_h - 12
        draw.rounded_rectangle([st_bx, st_by, st_bx+st_bw, st_by+st_bh], radius=4, fill=bg)
        draw.text((x_right+g_c1+g_c2 + g_c3/2, y_right + r_h/2 - 1), s_text.title() if s_text != "PASSED" else "Passed", font=F_BADGE, fill=fg, anchor="mm")
        
        y_right += r_h

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
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
