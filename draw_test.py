from PIL import Image, ImageDraw, ImageFont

img_path = "./assets/template_coe_blank.png"
out_path = "/Users/fa-12044/.gemini/antigravity/brain/54e15afc-f2ed-4305-a38a-c98cec02b77e/artifacts/debug_cert.jpg"

if __name__ == "__main__":
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Let's draw some red boxes to see where things are
    # Y from 2000 to 2400 step 50
    for y in range(2000, 2450, 50):
        draw.rectangle([200, y, 900, y+10], fill="red")
        
    img.save(out_path, format="JPEG", quality=80)
