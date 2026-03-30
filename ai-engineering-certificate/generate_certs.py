#!/usr/bin/env python3
"""
Certificate Generator - AI Engineering Bootcamp Batch 10
=========================================================
Rules:
  - Certificate of Completion (COC) : Atc (Accum) col >= 70%
  - Certificate of Excellence (COE) : Current Score col >= 70
  - Best Student (COE special)       : 1 student with "excellence" grade only
                                       → highest Current Score among COE receivers

Output:
  generated/completion/  — individual HTML files (COC)
  generated/excellence/  — individual HTML files (COE)
  generated/best/        — 1 HTML file for best student
  generated/summary.csv  — list of all students & cert type issued
"""

import csv
import os
import re
import shutil
import random
import string
from pathlib import Path
from playwright.sync_api import sync_playwright

# ─── CONFIG ───────────────────────────────────────────────────────────────────
CSV_FILE   = "Tracker Score Recap - Live Bootcamp AI Engineering Batch 10 - Student Report.csv"
TEMPLATE   = "index.html"
BATCH      = "10"
ISSUANCE   = "Jakarta, 23 Maret 2026"
OUTPUT_DIR = Path("generated")

# Credential ID format: REA/DDMMYYYY/B10/{TYPE}/{SEQ}
# TYPE: C = Completion, E = Excellence
DATE_CODE  = "23032026"


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def pct_to_float(val: str) -> float:
    """Convert '93%' → 93.0  or '0' → 0.0"""
    val = val.strip()
    if val.endswith('%'):
        return float(val[:-1])
    try:
        return float(val)
    except ValueError:
        return 0.0


def safe_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    return re.sub(r'[\\/*?:"<>|]', '', name).strip().replace(' ', '_')


def load_template() -> str:
    with open(TEMPLATE, encoding='utf-8') as f:
        return f.read()


_used_cert_ids: set = set()

def make_cert_id(batch: str) -> str:
    """Generate a fresh unique certificate number: REAENG{BATCH}XXXXX (5 random alphanum uppercase)"""
    chars = string.ascii_uppercase + string.digits
    while True:
        suffix = ''.join(random.choices(chars, k=5))
        cert_id = f"REAENG{batch}{suffix}"
        if cert_id not in _used_cert_ids:
            _used_cert_ids.add(cert_id)
            return cert_id


def generate_html(template: str, **kwargs) -> str:
    """Simple placeholder substitution."""
    html = template
    for key, val in kwargs.items():
        html = html.replace('{{' + key + '}}', str(val))
    return html


# ─── PDF CONVERSION ─────────────────────────────────────────────────────────
def html_to_pdf(html_path: Path) -> Path:
    """Convert an HTML file to PDF via Playwright Chromium.
    Deletes the HTML after conversion. Returns the PDF path."""
    pdf_path = html_path.with_suffix('.pdf')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 848})
        page.goto(html_path.resolve().as_uri())
        page.wait_for_load_state('networkidle')
        page.pdf(
            path=str(pdf_path),
            format='A4',
            landscape=True,
            print_background=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
        )
        browser.close()
    html_path.unlink()  # remove intermediate HTML
    return pdf_path


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    # Prepare output dirs
    for sub in ['completion', 'excellence', 'best']:
        (OUTPUT_DIR / sub).mkdir(parents=True, exist_ok=True)

    template = load_template()

    students = []
    with open(CSV_FILE, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys & values
            row = {k.strip(): v.strip() for k, v in row.items()}
            students.append(row)

    summary_rows = []


    # We need to determine best student BEFORE generating all certs
    # Best student = among COE eligible (Current Score >=70), highest score
    # If tie → pick smallest No (first in list)
    coe_eligible = [
        s for s in students
        if s.get('Current Score', '') and
           float(s['Current Score']) >= 70
    ]
    best_student = None
    if coe_eligible:
        best_student = max(coe_eligible, key=lambda s: float(s['Current Score']))

    best_student_id = best_student['Student ID'] if best_student else None

    for student in students:
        name         = student.get('Name', '').strip()
        student_id   = student.get('Student ID', '').strip()
        cert_id      = make_cert_id(BATCH)   # one ID shared for both COC & COE
        atc_str      = student.get('Atc (Accum)', '0%')
        score_str    = student.get('Current Score', '0')
        grade        = student.get('Current Grade', '')

        atc_val   = pct_to_float(atc_str)
        score_val = float(score_str) if score_str else 0.0

        gets_coe = score_val >= 70
        gets_coc = atc_val >= 70 or gets_coe
        is_best  = (student_id == best_student_id)

        issued = []

        # ── Certificate of Excellence (+ Best Student override) ──
        if gets_coe:

            if is_best:
                theme       = 'theme-excellence'
                cert_type   = 'CERTIFICATE OF EXCELLENCE'
                description = (
                    f'For demonstrating exceptional dedication, fulfilling all comprehensive curriculum requirements, and '
                    f'successfully delivering an outstanding final project, thereby earning the status of '
                    f'<span class="status status-best">BEST STUDENT</span> in the following program:'
                )
            else:
                theme       = 'theme-excellence'
                cert_type   = 'CERTIFICATE OF EXCELLENCE'
                description = (
                    f'For demonstrating exceptional dedication and successfully fulfilling all curriculum requirements '
                    f'with a score of <span class="status status-best">{int(score_val)}</span>, '
                    f'thereby earning the grade of <span class="status status-best">{grade}</span> in the following program:'
                )

            html = generate_html(
                template,
                THEME_CLASS      = theme,
                CERT_TYPE        = cert_type,
                NAMA             = name,
                DESCRIPTION_HTML = description,
                BATCH            = BATCH,
                TANGGAL          = ISSUANCE,
                NO_SERTIFIKAT    = cert_id,
            )

            fname = f"{safe_filename(name)}_COE.html"
            if is_best:
                out_path = OUTPUT_DIR / 'best' / fname
            else:
                out_path = OUTPUT_DIR / 'excellence' / fname
            out_path.write_text(html, encoding='utf-8')
            pdf = html_to_pdf(out_path)
            print(f"  ✓ {'BEST' if is_best else 'COE'}: {pdf.name}")

            issued.append('COE (Best Student)' if is_best else 'COE')

        # ── Certificate of Completion ──
        if gets_coc:

            theme       = 'theme-completion'
            cert_type   = 'CERTIFICATE OF COMPLETION'
            description = (
                f'For demonstrating strong commitment and successfully fulfilling the attendance requirements '
                f'with an accumulation score of <span class="status status-passed">{atc_str}</span> throughout the sessions, '
                f'thereby earning the status of <span class="status status-passed">PASSED</span> in the following program:'
            )

            html = generate_html(
                template,
                THEME_CLASS      = theme,
                CERT_TYPE        = cert_type,
                NAMA             = name,
                DESCRIPTION_HTML = description,
                BATCH            = BATCH,
                TANGGAL          = ISSUANCE,
                NO_SERTIFIKAT    = cert_id,
            )

            fname    = f"{safe_filename(name)}_COC.html"
            out_path = OUTPUT_DIR / 'completion' / fname
            out_path.write_text(html, encoding='utf-8')
            pdf = html_to_pdf(out_path)
            print(f"  ✓ COC: {pdf.name}")

            issued.append('COC')

        if not issued:
            issued.append('—')

        summary_rows.append({
            'No'           : student.get('No', ''),
            'Student ID'   : student_id,
            'Name'         : name,
            'Atc (Accum)'  : atc_str,
            'Current Score': score_str,
            'Grade'        : grade,
            'Gets COC'     : 'YES' if gets_coc else 'NO',
            'Gets COE'     : 'YES' if gets_coe else 'NO',
            'Best Student' : 'YES' if is_best else 'NO',
            'Certs Issued' : ', '.join(issued),
        })

    # Write summary CSV
    summary_path = OUTPUT_DIR / 'summary.csv'
    with open(summary_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['No','Student ID','Name','Atc (Accum)','Current Score','Grade',
                      'Gets COC','Gets COE','Best Student','Certs Issued']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    # Print stats
    total      = len(students)
    coc_count  = sum(1 for r in summary_rows if r['Gets COC'] == 'YES')
    coe_count  = sum(1 for r in summary_rows if r['Gets COE'] == 'YES')

    print("=" * 60)
    print("  AI Engineering Batch 10 — Certificate Generator")
    print("=" * 60)
    print(f"  Total students   : {total}")
    print(f"  COC recipients   : {coc_count}  (Atc ≥ 70%)")
    print(f"  COE recipients   : {coe_count}  (Current Score ≥ 70)")
    print(f"  Best Student     : {best_student['Name'] if best_student else 'N/A'}")
    print(f"                     Score: {best_student['Current Score'] if best_student else '-'}")
    print(f"\n  Output folder    : {OUTPUT_DIR.resolve()}")
    print(f"  Summary CSV      : {summary_path.resolve()}")
    print("=" * 60)


if __name__ == '__main__':
    main()
