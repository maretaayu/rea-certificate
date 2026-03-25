"""
One-time script to patch the 'skillacademy.com/verify' URL in the
certificate template PNG files so the fill blends invisibly with background.

Strategy:
  - For each X column in the erase zone, sample the colour from just ABOVE
    the erase rectangle (y = ERASE_Y0 - 1). This perfectly follows the
    original gradient of the template, making the patch invisible.
  - No flat fill, no pattern — just the natural background.

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

    # ── 1. Column-by-column fill using colour from just above erase zone ─
    # This perfectly reproduces the original gradient.
    ref_y = ERASE_Y0 - 1  # row just above the erase area
    for x in range(ERASE_X0, ERASE_X1 + 1):
        col_color = px[x, ref_y]
        for y in range(ERASE_Y0, ERASE_Y1 + 1):
            px[x, y] = col_color

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
    for tmpl in ["assets/template_coe_blank.png", "assets/template_coc_blank.png"]:
        if os.path.exists(tmpl):
            patch(tmpl)
        else:
            print(f"SKIP: {tmpl} not found")
    print("\nDone!")
