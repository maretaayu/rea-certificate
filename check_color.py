from PIL import Image
import os

img_path = 'assets/Sertifikat Webinar KODING KURMA_Sertifikat Peserta_2.jpg'
if os.path.exists(img_path):
    img = Image.open(img_path)
    print("Center pixel 1:", img.getpixel((1750, 1400)))
    print("Center pixel 2:", img.getpixel((1750, 1500)))
    print("Center pixel 3:", img.getpixel((1750, 1600)))
    print("Off-center pixel 1:", img.getpixel((1000, 1500)))
    print("Off-center pixel 2:", img.getpixel((2500, 1500)))
