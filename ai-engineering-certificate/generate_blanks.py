"""
Generate blank templates for COC and COE using Playwright locally.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = BASE_DIR / "index.html"

def load_template() -> str:
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        return f.read()

def render_blank(cert_type_label: str) -> str:
    template = load_template()
    # Leave texts mostly blank
    if cert_type_label == "BEST" or cert_type_label == "COE":
        theme = "theme-excellence"
        cert_type = "CERTIFICATE OF EXCELLENCE"
    else:
        theme = "theme-completion"
        cert_type = "CERTIFICATE OF COMPLETION"

    html = template
    html = html.replace('{{THEME_CLASS}}', theme)
    html = html.replace('{{CERT_TYPE}}', cert_type)
    html = html.replace('{{NAMA}}', '')
    html = html.replace('{{DESCRIPTION_HTML}}', '')
    html = html.replace('{{BATCH}}', '10')
    html = html.replace('{{TANGGAL}}', 'Jakarta, 23 Maret 2026')
    html = html.replace('{{NO_SERTIFIKAT}}', '')
    
    # Replace CDN back to local assets just for local template generation if needed,
    # actually CDN is fine, Playwright will fetch them.
    return html

def save_blank_screenshot(html: str, out_name: str):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(html)
        tmp_path = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1200, 'height': 848}, device_scale_factor=2)
            page.goto(tmp_path.resolve().as_uri())
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(BASE_DIR / "assets" / out_name))
            browser.close()
    finally:
        tmp_path.unlink()

def main():
    print("Generating COE blank...")
    save_blank_screenshot(render_blank("COE"), "template_coe_blank.png")
    print("Generating COC blank...")
    save_blank_screenshot(render_blank("COC"), "template_coc_blank.png")
    print("Done!")

if __name__ == '__main__':
    main()
