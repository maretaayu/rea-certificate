"""
One-time script to patch the 'skillacademy.com/verify' URL in the
certificate template PNG files.

Run once:  python patch_template.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH_REG = "PlusJakartaSans-Regular.ttf"

def patch_template(img_path, out_path=None):
    if out_path is None:
        out_path = img_path

    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size
    print(f"INFO: {img_path} → size: {width}x{height}")

    # ─── Auto-detect the blue URL in the bottom-left quarter ─────────────
    # Scan bottom 40% of image, left 45% of width for blue-ish pixels
    scan_y_start = int(height * 0.60)
    scan_x_end   = int(width  * 0.45)

    blue_pixels = []
    for y in range(scan_y_start, height):
        for x in range(0, scan_x_end):
            r, g, b = img.getpixel((x, y))
            # Looks for typical hyperlink blue: high B, medium G, very low R
            if b > 160 and r < 80 and g < 180 and (b - r) > 90:
                blue_pixels.append((x, y))

    if not blue_pixels:
        print("  WARNING: No blue URL pixels found. Skipping.")
        return

    xs = [p[0] for p in blue_pixels]
    ys = [p[1] for p in blue_pixels]
    bx_min, bx_max = min(xs), max(xs)
    by_min, by_max = min(ys), max(ys)
    print(f"  Found blue URL pixels at x={bx_min}-{bx_max}, y={by_min}-{by_max}")

    # ─── Sample background colour just to the left of the URL ──────────
    sample_x = max(0, bx_min - 5)
    sample_y = (by_min + by_max) // 2
    bg_color = img.getpixel((sample_x, sample_y))
    print(f"  Background colour sampled: rgb{bg_color}")

    # ─── Erase old URL with a solid rectangle ────────────────────────────
    # Add padding around detected area
    pad_x, pad_y = 4, 6
    draw.rectangle(
        [bx_min - pad_x, by_min - pad_y, bx_max + pad_x, by_max + pad_y],
        fill=bg_color
    )

    # ─── Write new URL ───────────────────────────────────────────────────
    font_size = (by_max - by_min) + 8  # Roughly match original text height
    try:
        font = ImageFont.truetype(FONT_PATH_REG, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Draw the prefix in muted colour and the link in standard blue  
    prefix = "Verify authenticity at "
    link   = "ruangguru.com/rea/verify"

    # Sample grey text color from nearby grey text above the blue URL
    draw.text((bx_min, by_min - 2), prefix, font=font, fill="#94a3b8")
    prefix_w = int(font.getlength(prefix))
    draw.text((bx_min + prefix_w, by_min - 2), link, font=font, fill="#0284c7")

    img.save(out_path, format="PNG")
    print(f"  Saved → {out_path}")


if __name__ == "__main__":
    templates = [
        "assets/template_coe_blank.png",
        "assets/template_coc_blank.png",
    ]
    for t in templates:
        if os.path.exists(t):
            patch_template(t)
        else:
            print(f"SKIP: {t} not found")

    print("\nDone! Commit the patched PNGs to git.")
