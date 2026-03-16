import cv2
import numpy as np

img_path = 'assets/Sertifikat Webinar KODING KURMA_Sertifikat Peserta_2.jpg'
output_path = 'assets/template_clean.jpg'

print("Membaca gambar...")
img = cv2.imread(img_path)

if img is None:
    print("Gagal membaca gambar.")
    exit()

# Area teks (Y_START, Y_END), (X_START, X_END)
y1, y2 = 1100, 1850
x1, x2 = 500, 3000

print("Membuat mask...")
roi = img[y1:y2, x1:x2]

# Cari pixel yang lebih gelap (teksnya)
# Background kan terang RGB > 240, Teks gelap (abu gelap/hitam)
gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
_, mask = cv2.threshold(gray_roi, 150, 255, cv2.THRESH_BINARY_INV)

print("Inpainting teks lama (ini memakan waktu 10-20 detik)...")
# cv2.INPAINT_TELEA atau INPAINT_NS
roi_cleaned = cv2.inpaint(roi, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

# Kembalikan ke gambar asli
img[y1:y2, x1:x2] = roi_cleaned

print("Menyimpan hasil ke", output_path)
cv2.imwrite(output_path, img)
print("Selesai! Kamu punya template kosong baru bernama 'template_clean.jpg'")
