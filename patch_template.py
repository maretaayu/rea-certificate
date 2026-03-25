"""
One-time script to patch the 'skillacademy.com/verify' URL in the
certificate template PNG files.

Run once:  python patch_template.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH_REG  = "PlusJakartaSans-Regular.ttf"
FONT_PATH_BOLD = "PlusJakartaSans-Bold.ttf"

# From pixel analysis:
# Line 1 (gray):  "This credential verifies..."       y=1382-1394
# Line 2 (gray):  "completion of the boot camp."      y=1413-1430
# Line 3 (blue):  "Verify authenticity at ..."        y=1447-1475
# Font height of line 3 ≈ 28px.

# We want to:
#   1. Erase line 3 completely (fill with background colour)
#   2. Write a new line 3 with the same approximate font size but correct URL
#   
# Lines 1 & 2 are left as-is (they are already correct).

BG_COLOR   = "#e0f4fe"   # Background gradient colour at the footer area
GRAY_COLOR = "#94a3b8"   # Same muted colour as original gray text
BLUE_COLOR = "#0284c7"   # Same blue as original link

ERASE_RECT = (260, 1435, 800, 1485)  # Covers line 3 including descenders
TEXT_Y     = 1445                    # Baseline for new text (top of glyph)
TEXT_X     = 273                     # Left margin
FONT_SIZE  = 27                      # Matches the ~28px character height found in scan


def patch(img_path: str) -> None:
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 1. Erase old blue URL ────────────────────────────────────────────
    draw.rectangle(list(ERASE_RECT), fill=BG_COLOR)

    # ── 2. Write replacement text ────────────────────────────────────────
    try:
        font = ImageFont.truetype(FONT_PATH_REG, FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    prefix = "Verify authenticity at "
    link   = "ruangguru.com/rea/verify"

    draw.text((TEXT_X, TEXT_Y), prefix, font=font, fill=GRAY_COLOR)
    prefix_w = int(font.getlength(prefix))
    draw.text((TEXT_X + prefix_w, TEXT_Y), link, font=font, fill=BLUE_COLOR)

    img.save(img_path, format="PNG")
    print(f"Patched → {img_path}")


if __name__ == "__main__":
    for tmpl in ["assets/template_coe_blank.png", "assets/template_coc_blank.png"]:
        if os.path.exists(tmpl):
            patch(tmpl)
        else:
            print(f"SKIP: {tmpl} not found")
    print("\nDone! Commit the patched PNGs to git.")
