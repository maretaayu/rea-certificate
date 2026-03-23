"""
REA AI Engineering Certificate API
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
    PDF binary (Content-Type: application/pdf)
    Header X-Cert-ID: REAENG10XXXXX

GET /health  →  health check
"""

import os
import io
import re
import random
import string
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from playwright.sync_api import sync_playwright

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH  = BASE_DIR / "index.html"
BATCH          = "10"
ISSUANCE       = "Jakarta, 23 Maret 2026"

CDN = {
    "logo_rea" : "https://cdn-web.ruangguru.com/file-uploader/4791f896-8bc7-41d4-9c58-67c9c4054477.png",
    "logo_sa"  : "https://cdn-web.ruangguru.com/file-uploader/a287e3f7-3d52-477e-826b-80789f3d9861.png",
    "signature": "https://cdn-web.ruangguru.com/file-uploader/cd39c2fc-e6b9-4841-9f85-e55edabc8702.png",
    "stamp"    : "https://cdn-web.ruangguru.com/file-uploader/3658b378-4a25-4f95-926e-6fbd9a28ce3a.png",
}

# ─── APP ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "REA Certificate API",
    description = "Generate PDF certificates for AI Engineering Bootcamp Batch 10",
    version     = "2.0.0",
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
    student_id    : str
    atc_accum     : str             = "0%"   # e.g. "93%"
    current_score : float           = 0      # e.g. 89
    current_grade : str             = ""     # e.g. "A"
    cert_type     : Optional[str]   = None   # "COC" | "COE" | "BEST" (auto if None)
    batch         : str             = BATCH
    issuance_date : str             = ISSUANCE

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def pct_to_float(val: str) -> float:
    val = val.strip()
    if val.endswith('%'):
        return float(val[:-1])
    try:
        return float(val)
    except ValueError:
        return 0.0


def make_cert_id(batch: str) -> str:
    chars = string.ascii_uppercase + string.digits
    return f"REAENG{batch}" + ''.join(random.choices(chars, k=5))


def load_template() -> str:
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        return f.read()


def render_cert(
    cert_type_label : str,   # "COC" | "COE" | "BEST"
    name            : str,
    cert_id         : str,
    atc_str         : str,
    score           : float,
    grade           : str,
    batch           : str,
    issuance_date   : str,
) -> str:
    template = load_template()

    if cert_type_label == "BEST":
        theme       = "theme-excellence"
        cert_type   = "CERTIFICATE OF EXCELLENCE"
        description = (
            'For demonstrating exceptional dedication, fulfilling all comprehensive curriculum requirements, and '
            'successfully delivering an outstanding final project, thereby earning the status of '
            '<span class="status status-best">BEST STUDENT</span> in the following program:'
        )
    elif cert_type_label == "COE":
        theme       = "theme-excellence"
        cert_type   = "CERTIFICATE OF EXCELLENCE"
        description = (
            f'For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements '
            f'with a score of <span class="status status-best">{int(score)}</span>, '
            f'thereby earning the grade of <span class="status status-best">{grade}</span> in the following program:'
        )
    else:  # COC
        theme       = "theme-completion"
        cert_type   = "CERTIFICATE OF COMPLETION"
        description = (
            f'For demonstrating strong commitment and successfully fulfilling the attendance requirements '
            f'with an accumulation score of <span class="status status-passed">{atc_str}</span> throughout the sessions, '
            f'thereby earning the status of <span class="status status-passed">PASSED</span> in the following program:'
        )

    html = template
    html = html.replace('{{THEME_CLASS}}',      theme)
    html = html.replace('{{CERT_TYPE}}',        cert_type)
    html = html.replace('{{NAMA}}',             name)
    html = html.replace('{{DESCRIPTION_HTML}}', description)
    html = html.replace('{{BATCH}}',            batch)
    html = html.replace('{{TANGGAL}}',          issuance_date)
    html = html.replace('{{NO_SERTIFIKAT}}',    cert_id)
    return html


def html_to_pdf_bytes(html: str) -> bytes:
    """Write HTML to temp file, render via Playwright, return PDF bytes."""
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(html)
        tmp_path = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1200, 'height': 848})
            page.goto(tmp_path.resolve().as_uri())
            page.wait_for_load_state('networkidle')
            pdf_bytes = page.pdf(
                format='A4',
                landscape=True,
                print_background=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            )
            browser.close()
        return pdf_bytes
    finally:
        tmp_path.unlink(missing_ok=True)


# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "batch": BATCH}


@app.post("/generate_cert")
def generate_cert(req: CertRequest):
    """
    Generate a certificate PDF.

    Auto-detect cert_type if not provided:
      - "BEST" if current_score == 100 and cert_type == "BEST"
      - "COE"  if current_score >= 70
      - "COC"  if atc_accum >= 70%

    Returns PDF binary.
    """
    atc_val   = pct_to_float(req.atc_accum)
    score_val = float(req.current_score)

    # Determine cert type
    cert_type = (req.cert_type or "").upper()

    if cert_type not in ("COC", "COE", "BEST"):
        # Auto-detect
        if score_val >= 70:
            cert_type = "COE"
        elif atc_val >= 70:
            cert_type = "COC"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Student tidak memenuhi syarat: Atc={req.atc_accum}, Score={req.current_score}"
            )

    # Validate eligibility
    if cert_type == "COE" and score_val < 70:
        raise HTTPException(status_code=400, detail="COE requires Current Score >= 70")
    if cert_type == "COC" and atc_val < 70:
        raise HTTPException(status_code=400, detail="COC requires Atc (Accum) >= 70%")

    cert_id  = make_cert_id(req.batch)
    html     = render_cert(
        cert_type_label = cert_type,
        name            = req.name,
        cert_id         = cert_id,
        atc_str         = req.atc_accum,
        score           = score_val,
        grade           = req.current_grade,
        batch           = req.batch,
        issuance_date   = req.issuance_date,
    )
    pdf_bytes = html_to_pdf_bytes(html)

    filename = f"{req.name.replace(' ', '_')}_{cert_type}.pdf"
    return Response(
        content      = pdf_bytes,
        media_type   = "application/pdf",
        headers      = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Cert-ID"          : cert_id,
            "X-Cert-Type"        : cert_type,
            "X-Student-Name"     : req.name,
        }
    )
