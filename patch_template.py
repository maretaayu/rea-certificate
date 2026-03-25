"""
One-time script to patch the 'skillacademy.com/verify' URL in the
certificate template PNG files.

Run once:  python patch_template.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH_REG  = "PlusJakartaSans-Regular.ttf"

# From pixel analysis:
# Line 1 (gray):  "This credential verifies..."       y=1382-1394, font ~16px
# Line 2 (gray):  "completion of the boot camp."      y=1413-1430
# Line 3 (blue):  "Verify authenticity at ..."        y=1447-1475, rightmost x=1130
#
# We need to erase EVERYTHING in line 3's band (including any previous patches)
# and rewrite it at the matching font size.

BG_COLOR   = "#e0f4fe"   # Background gradient colour at footer area
GRAY_COLOR = "#94a3b8"   # Same muted grey as "Verify authenticity at"
BLUE_COLOR = "#0284c7"   # Same blue as original link

# Erase rect — wider than rightmost detected pixel to be safe
ERASE_RECT = (260, 1435, 1160, 1490)

TEXT_Y     = 1447    # Top of glyph for new text
TEXT_X     = 273     # Left margin
FONT_SIZE  = 16      # Matches gray text height from pixel analysis


def patch(img_path: str) -> None:
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 1. Erase old URL (and any previous patch attempt) ──────────────
    draw.rectangle(list(ERASE_RECT), fill=BG_COLOR)

    # ── 2. Write replacement text ──────────────────────────────────────
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
    print("\nDone!")
