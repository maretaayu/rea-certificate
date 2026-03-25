"""
Patch the 'skillacademy.com/verify' URL in certificate template PNGs.

Strategy:
  - Interpolate gradient left-to-right (horizontal interpolation) for EVERY
    row in the erase zone.
  - For a coordinate (x,y), the colour blends from the pixel just left
    of the erase zone to the pixel just right of the erase zone.
  - This mathematically eliminates all hard edges and completely recreates the
    original diagonal gradient beneath the text.

Run once:  python patch_template.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH_REG = "PlusJakartaSans-Regular.ttf"

GRAY_COLOR = "#94a3b8"
BLUE_COLOR = "#0284c7"

ERASE_X0, ERASE_X1 = 260, 1160
ERASE_Y0, ERASE_Y1 = 1435, 1490

TEXT_Y    = 1449
TEXT_X    = 273
FONT_SIZE = 20

def patch(img_path: str) -> None:
    img = Image.open(img_path).convert("RGB")
    px  = img.load()
    draw = ImageDraw.Draw(img)

    total_w = ERASE_X1 - ERASE_X0

    # ── 1. Create seamless gradient blending left edge and right edge ─────
    for y in range(ERASE_Y0, ERASE_Y1 + 1):
        # We sample the colors just outside our erase box for this specific row.
        # This gives us perfect alignment with the vertical gradient change.
        left_color = px[ERASE_X0 - 1, y]
        right_color = px[ERASE_X1 + 1, y]
        
        for x in range(ERASE_X0, ERASE_X1 + 1):
            t = (x - ERASE_X0) / total_w
            # Blend RGB channels linearly
            r = int(left_color[0] * (1 - t) + right_color[0] * t)
            g = int(left_color[1] * (1 - t) + right_color[1] * t)
            b = int(left_color[2] * (1 - t) + right_color[2] * t)
            px[x, y] = (r, g, b)

    # ── 2. Write replacement URL ─────────────────────────────────────────
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
    # If the original unmodified templates exist (e.g. from git stash/checkout),
    # this will patch them flawlessly. Otherwise, it will repair the currently
    # padded images by pulling colors from outside the ERASE zone.
    for tmpl in ["assets/template_coe_blank.png", "assets/template_coc_blank.png"]:
        if os.path.exists(tmpl):
            patch(tmpl)
        else:
            print(f"SKIP: {tmpl} not found")
    print("\nDone!")
