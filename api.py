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

FONT_BOLD = str(BASE_DIR / "PlusJakartaSans-Bold.ttf")
FONT_REG  = str(BASE_DIR / "PlusJakartaSans-Regular.ttf")

def get_font(path, size): 
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

F_H1   = get_font(FONT_BOLD, 42)
F_H2   = get_font(FONT_BOLD, 28)
F_LBL  = get_font(FONT_BOLD, 14)
F_VAL  = get_font(FONT_BOLD, 20)
F_BIG  = get_font(FONT_BOLD, 54)
F_BODY = get_font(FONT_REG,  16)
F_B_B  = get_font(FONT_BOLD, 16)

app = FastAPI(
    title="REA API",
    description="REA AI Engineering Certificate & Student Report API (PIL Native Version)",
    version="4.0.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CertRequest(BaseModel):
    name: str; student_id: str; batch: str = BATCH
    atc_accum: Union[str, float] = "0%"; current_score: Union[str, float] = 0
    current_grade: str = ""; cert_type: Optional[str] = None

class ReportRequest(BaseModel):
    name: str; student_id: str; batch: str = BATCH
    current_score: Union[str, float] = 0; current_grade: str = ""; current_status: str = ""
    atc_accum: Union[str, float] = "0%"; pre_test: str = "—"; post_test: str = "—"; fp: str = "—"
    atr1: str = "—"; prj1: str = "—"; atr2: str = "—"; prj2: str = "—"; atr3: str = "—"; prj3: str = "—"
    atr4: str = "—"; prj4: str = "—"; atr5: str = "—"; atr6: str = "—"; atr7: str = "—"

def draw_report_v4(req: ReportRequest) -> bytes:
    W, H = 842, 1191 # A4 @ 72 DPI-ish
    img = Image.new('RGB', (W, H), '#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Header: Deep Navy
    draw.rectangle([0, 0, W, 180], fill="#0A192F")
    draw.text((50, 60),  "Student Report", font=F_H1, fill="#FFFFFF")
    draw.text((50, 110), f"AI ENGINEERING BOOTCAMP • BATCH {req.batch}", font=get_font(FONT_BOLD, 14), fill="#3B82F6")
    
    # Content Section
    y = 220
    def box(x, label, val, w):
        draw.rectangle([x, y, x+w, y+100], outline="#E5E7EB", width=2)
        draw.text((x+15, y+15), label.upper(), font=F_LBL, fill="#9CA3AF")
        draw.text((x+15, y+45), str(val), font=F_VAL, fill="#111827")

    box(50,  "Student Name", req.name, 350)
    # Subtitle for name box
    draw.text((50+15, y+75), f"Batch {req.batch} · AI Engineering Bootcamp", font=get_font(FONT_REG, 11), fill="#6B7280")
    
    box(410, "Student ID", req.student_id, 150)
    box(570, "Score", str(req.current_score), 100)
    box(680, "Grade", req.current_grade, 100)
    
    # Badge
    st = str(req.current_status).upper()
    bc = {"PASSED": ("#DCFCE7","#166534"), "FAILED": ("#FEE2E2","#991B1B")}.get(st, ("#F3F4F6","#374151"))
    draw.rounded_rectangle([50, 330, 200, 360], radius=5, fill=bc[0])
    draw.text((125, 345), st, font=get_font(FONT_BOLD, 12), fill=bc[1], anchor="mm")

    # Table: Attendance 
    ty = 400
    draw.rectangle([50, ty, W-50, ty+40], fill="#F9FAFB")
    draw.line([(50, ty), (50, ty+40)], fill="#3B82F6", width=5)
    draw.text((65, ty+10), "ATTENDANCE & PROJECT RECAP", font=get_font(FONT_BOLD, 18), fill="#111827")
    
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
    draw.text((65, sy+10), "SCORE RECAP", font=get_font(FONT_BOLD, 18), fill="#111827")
    sy += 50
    recap = [("Pre Test", req.pre_test), ("Post Test", req.post_test), ("Attendance", req.atc_accum), ("Capstone", req.fp)]
    for lbl, val in recap:
        draw.text((65, sy), lbl, font=F_BODY, fill="#374151")
        draw.text((W-120, sy), fv(val), font=F_B_B, fill="#000000", anchor="mm")
        sy += 35

    buf = io.BytesIO(); img.save(buf, format="PNG", quality=95); buf.seek(0)
    return buf.read()

@app.post("/generate_cert")
def cert(req: CertRequest):
    # Determine certificate type
    score = float(str(req.current_score))
    is_coe = score >= 70
    template = TEMPLATE_COE if is_coe else TEMPLATE_COC
    
    img = Image.open(template).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Coordinates (Approximate based on known good layout)
    # Name: (Center horizontally?) In the image it's slightly to the left or centered.
    # Logic in previous version used (260, 620). Let's stick with that for name.
    
    # 1. Name
    draw.text((260, 620), req.name, font=get_font(FONT_BOLD, 80), fill="#1e293b")
    
    # 2. Detailed Description ("Passed" etc)
    if is_coe:
        desc = (
            f"For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements "
            f"with a score of {score}, thereby earning the grade of {req.current_grade} in the following program:"
        )
    else:
        desc = (
            f"For demonstrating strong commitment and successfully fulfilling the attendance requirements "
            f"with an accumulation score of {req.atc_accum} throughout the sessions, thereby earning the status "
            f"of PASSED in the following program:"
        )
    
    # Wrap text and draw
    desc_wrapped = textwrap.fill(desc, width=90)
    draw.multiline_text((260, 750), desc_wrapped, font=get_font(FONT_REG, 24), fill="#334155", spacing=10)

    # 3. Program Name / Batch Info
    prog_text = f"AI Engineering Bootcamp Batch {req.batch}"
    draw.text((260, 920), prog_text, font=get_font(FONT_BOLD, 40), fill="#1e293b")
    
    # 4. Date
    date_text = "Jakarta, 23 Maret 2026"
    draw.text((260, 1680), date_text, font=get_font(FONT_BOLD, 28), fill="#1e293b")
    
    # 4. Signature Tag (Alvin Francis Tamie)
    # In the image it's bottom right.
    # Not adding signature drawing yet as it requires an asset path in logic,
    # but the text is usually there in template.

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")

@app.post("/generate_report")
def report(req: ReportRequest):
    return Response(content=draw_report_v4(req), media_type="image/png")

