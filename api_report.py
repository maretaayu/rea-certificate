import os
import io
import json
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Union, Any
import uuid

# Playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    pass

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BATCH    = "10"

app = FastAPI(
    title       = "REA Report API",
    description = "Generate PNG Student Reports via Playwright",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    prj0          : Union[str, int, float] = ""
    prj1          : Union[str, int, float] = ""
    atr2          : Union[str, int, float] = ""
    prj2          : Union[str, int, float] = ""
    atr3          : Union[str, int, float] = ""
    prj3          : Union[str, int, float] = ""
    atr4          : Union[str, int, float] = ""
    prj4          : Union[str, int, float] = ""
    atr5          : Union[str, int, float] = ""
    prj5          : Union[str, int, float] = ""
    atr6          : Union[str, int, float] = ""
    atr7          : Union[str, int, float] = ""

    model_config = {
        "alias_generator": lambda s: s.replace("_", "").capitalize(),
        "populate_by_name": True,
        "extra": "ignore"
    }

def fmt_score(val) -> str:
    """Round numeric score to nearest integer for display."""
    s = str(val).strip()
    if not s or s in ('', '-1', '-', '—', '[empty]'):
        return '—'
    try:
        return str(round(float(s)))
    except ValueError:
        return s

def fmt_val(val) -> str:
    s = str(val).strip()
    if not s or s in ('', '-1', '-', '—', '[empty]'):
        return '—'
    try:
        f = float(s)
        if f < 0: return '—'
        return str(int(f)) if f == int(f) else s
    except ValueError:
        return s

def fmt_prj(val) -> tuple:
    """Returns (display_value, dim_class).
    Logic:
      - Empty / '-' / '—' / 'NA'  → project not started yet → 'Upcoming' (dim)
      - 0 (explicit)              → student did not submit  → '0'        (no dim)
      - numeric > 0               → actual score            → str        (no dim)
    """
    s = str(val).strip()
    if not s or s in ('-', '—', '-1', '[empty]') or s.upper() == 'NA':
        return ('Upcoming', 'dim')      # project not started / deadline not reached
    try:
        f = float(s)
        if f < 0:
            return ('Upcoming', 'dim')  # treat negative as not started
        return (str(int(f)) if f == int(f) else s, '')
    except ValueError:
        return (s, '')

def render_report_html(req: ReportRequest) -> bytes:
    with open(BASE_DIR / 'student-report' / 'index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    status_str = str(req.current_status).upper()
    status_classes = {
        "PASSED": "status-passed",
        "REMEDIAL": "status-remedial",
        "FAILED": "status-failed",
        "NEED IMPROVEMENT": "status-need-improvement",
    }
    status_class = status_classes.get(status_str, "status-passed")

    # Sheet column mapping: prj1→Course2, prj2→Course3, prj3→Course4, prj4→Course5
    # Course 1, 6, 7 have no project (handled as — in HTML)
    prj_courses = [
        (str(req.atr1), req.prj0),      # Course 1 ← prj0 from sheet
        (str(req.atr2), req.prj1),      # Course 2 ← prj1 from sheet
        (str(req.atr3), req.prj2),      # Course 3 ← prj2 from sheet
        (str(req.atr4), req.prj3),      # Course 4 ← prj3 from sheet
        (str(req.atr5), req.prj4),      # Course 5 ← prj4 from sheet
        (str(req.atr6), None),          # Course 6 — no project
        (str(req.atr7), None),          # Course 7 — no project
    ]

    post_test_val = fmt_val(req.post_test)
    fp_val        = fmt_val(req.fp)

    replacements = {
        '{{NAME}}':             str(req.name),
        '{{STUDENT_ID}}':       str(req.student_id),
        '{{BATCH}}':            str(req.batch),
        '{{CURRENT_SCORE}}':    fmt_score(req.current_score),
        '{{GRADE}}':            str(req.current_grade),
        '{{STATUS}}':           status_str,
        '{{STATUS_TAG_CLASS}}': status_class,
        '{{PRE_TEST}}':         fmt_val(req.pre_test),
        '{{POST_TEST}}':        post_test_val,
        '{{POST_DIM}}':         'dim' if post_test_val in ('—', 'NA') else '',
        '{{ATC_ACCUM}}':        str(req.atc_accum),
        '{{FP}}':               fp_val,
        '{{FP_DIM}}':           'dim' if fp_val in ('—', 'NA') else '',
    }

    for i, (atr, prj_raw) in enumerate(prj_courses, start=1):
        replacements['{{ATR' + str(i) + '}}'] = atr
        if prj_raw is not None:
            val, dim = fmt_prj(prj_raw)
            replacements['{{PRJ' + str(i) + '}}']         = val
            replacements['{{PRJ' + str(i) + '_DIM}}']     = dim

    for k, v in replacements.items():
        html = html.replace(k, v)

    base_href = f'<base href="file://{BASE_DIR}/student-report/">'
    html = html.replace('<head>', f'<head>\n    {base_href}')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page(viewport={'width': 850, 'height': 1200})
        page.set_content(html)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(600)
        png_bytes = page.locator('.page').screenshot()
        browser.close()

    return png_bytes

@app.post("/generate_report")
def generate_report(req: ReportRequest, format: Optional[str] = None):
    png_bytes = render_report_html(req)
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

@app.post("/debug_report")
def debug_report(req: ReportRequest):
    """Echo raw request payload — use this to inspect what n8n actually sends."""
    return req.model_dump()
