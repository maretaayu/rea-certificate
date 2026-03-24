import os
import io
import json
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
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

def fmt_val(val) -> str:
    s = str(val).strip()
    if not s or s in ('', '-1', '-', '—'):
        return '—'
    try:
        f = float(s)
        if f < 0: return '—'
        return str(int(f)) if f == int(f) else s
    except ValueError:
        return s

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

    courses = [
        (str(req.atr1), fmt_val(req.prj1)),
        (str(req.atr2), fmt_val(req.prj2)),
        (str(req.atr3), fmt_val(req.prj3)),
        (str(req.atr4), fmt_val(req.prj4)),
        (str(req.atr5), '—'),
        (str(req.atr6), '—'),
        (str(req.atr7), '—'),
    ]

    replacements = {
        '{{name}}': str(req.name),
        '{{student_id}}': str(req.student_id),
        '{{batch}}': str(req.batch),
        '{{score}}': str(req.current_score),
        '{{grade}}': str(req.current_grade),
        '{{status}}': status_str,
        '{{status_class}}': status_class,
        '{{pre_test}}': fmt_val(req.pre_test),
        '{{post_test}}': fmt_val(req.post_test),
        '{{atc_accum}}': str(req.atc_accum),
        '{{fp}}': fmt_val(req.fp),
    }

    for i, (atr, prj) in enumerate(courses, start=1):
        replacements[f'{{atr{i}}}'] = atr
        replacements[f'{{prj{i}}}'] = prj

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
