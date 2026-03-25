"""
One-time script to patch the 'skillacademy.com/verify' URL in the
certificate template PNG files.

Strategy:
  - Sample background pixels row-by-row to get natural gradient fill
  - Overlay a subtle dot grid that matches the certificate's existing pattern
  - Write the new URL text at a comfortable 20px font size

Run once:  python patch_template.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH_REG = "PlusJakartaSans-Regular.ttf"

GRAY_COLOR = "#94a3b8"
BLUE_COLOR = "#0284c7"

# From pixel analysis: line 3 is at y=1447-1475, rightmost text at x=1130
ERASE_X0, ERASE_X1 = 260, 1160
ERASE_Y0, ERASE_Y1 = 1435, 1490

TEXT_Y    = 1449
TEXT_X    = 273
FONT_SIZE = 20   # slightly bigger than the 16px gray text above, but still small


def patch(img_path: str) -> None:
    img  = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 1. Sample background gradient from undisturbed columns ──────────
    # Use x=1180 (just outside erase zone but same y rows) to sample the
    # natural gradient colour at each row, then fill the erase zone per-row.
    for y in range(ERASE_Y0, ERASE_Y1 + 1):
        # Sample a clean background column far to the right (past any text)
        r, g, b = img.getpixel((min(1200, img.width - 1), y))
        draw.line([(ERASE_X0, y), (ERASE_X1, y)], fill=(r, g, b))

    # ── 2. Overlay a subtle translucent dot grid (like template pattern) ─
    # Spacing: 26x26 px to echo the certificate's existing 28px diagonal grid
    dot_color_base = img.getpixel((700, 1460))          # background at midpoint
    dot_r = max(0, dot_color_base[0] - 12)              # slightly darker than bg
    dot_g = max(0, dot_color_base[1] - 8)
    dot_b = max(0, dot_color_base[2] - 4)
    dot_color = (dot_r, dot_g, dot_b)

    step = 26
    for y in range(ERASE_Y0 + 4, ERASE_Y1, step):
        for x in range(ERASE_X0 + 4, ERASE_X1, step):
            draw.ellipse([x, y, x + 2, y + 2], fill=dot_color)

    # ── 3. Write new URL ─────────────────────────────────────────────────
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
