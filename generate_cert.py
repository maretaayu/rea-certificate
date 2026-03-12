import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import urllib.request
import os

# ============== KONFIGURASI ===================
TEMPLATE_PATH = "assets/template_clean.jpg" # Menggunakan template yang sudah dibersihkan teksnya
SIGNATURE_PATH = "" # Kosongkan agar tidak ada tandatangan
CSV_PATH = "FEEDBACK & Presensi (Jawaban) - Form Responses 1.csv"
OUTPUT_DIR = "output/"

# Mapping Sesi Webinar (S1, S2, S3)
SESSIONS = {
    "S1": {
        "event_date_no": "28022026",
        "cert_date": "Jakarta, 7 Maret 2026",
        "topic": "Getting Started as an AI Engineer:\nCareer Paths, Portfolios, and Interviews"
    },
    "S2": {
        "event_date_no": "07032026",
        "cert_date": "Jakarta, 12 Maret 2026",
        "topic": "Practical AI Automation with N8N\nfor Real-World Workflows"
    },
    "S3": {
        "event_date_no": "14032026",
        "cert_date": "Jakarta, 14 Maret 2026",
        "topic": "Vibe Coding: From Zero to End-to-End\nFull-Stack Application with AI"
    }
}

# [PENTING] Kamu bisa sesuaikan koordinat letak tulisan di sini (X, Y)
# Resolusi template: 3509 x 2481
POS_NAMA = (1754, 1000)      # Posisi tengah tulisan nama (X=tengah, Y=di atas garis)
POS_SUBTITLE = (1754, 1280)  # Posisi tulisan "For actively participating in the webinar:"
POS_TOPIK = (1754, 1460)     # Posisi judul topik webinar (digeser sedikit ke bawah agar pas dengan 2 baris)
POS_TANGGAL = (1754, 1720)   # Posisi tanggal webinar
# Sesuaikan agar persis di tengah di atas text "Certificate number" di box kanan bawah
POS_NOMOR = (3200, 2330)     # Digeser lebih ke Kanan
POS_SIGNATURE = (1550, 1920) # Posisi peletakan gambar tandatangan (jika ada)

SIGNATURE_RESIZE = (450, 250) # Ubah ukuran (lebar, tinggi) untuk file tandatangannya
FONT_NAMA_SIZE = 120       # Dikecilkan agar nama panjang tidak terpotong (dari 160 -> 120)
FONT_TOPIK_SIZE = 75       # Diperbesar
FONT_TANGGAL_SIZE = 60     # Diperbesar
FONT_NOMOR_SIZE = 55       # Diperbesar agar mirip screenshot

FONT_NAMA_COLOR = "#000000"  # Warna Hitam
FONT_TOPIK_COLOR = "#000000" # Warna Hitam
FONT_TEXT_COLOR = "#000000"  # Warna Hitam (untuk subtitle, tanggal)
FONT_NOMOR_COLOR = "#000000" # Warna Hitam
# ===============================================

def ensure_fonts():
    """Mengunduh font otomatis jika tidak ada di folder"""
    url_bold = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf"
    if not os.path.exists("Montserrat-Bold.ttf"):
        print("Mendownload font Montserrat-Bold...")
        try:
            urllib.request.urlretrieve(url_bold, "Montserrat-Bold.ttf")
        except Exception as e:
            print(f"Gagal download font: {e}. Kamu bisa pakai font lokal dengan mengganti nama fontnya di script.")

    url_regular = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Regular.ttf"
    if not os.path.exists("Montserrat-Regular.ttf"):
        print("Mendownload font Montserrat-Regular...")
        try:
            urllib.request.urlretrieve(url_regular, "Montserrat-Regular.ttf")
        except Exception as e:
            pass

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Validasi Berkas Inti
    if not os.path.exists(TEMPLATE_PATH):
        print(f"\n[ERROR] Template gambar tidak ditemukan!")
        print(f"Mohon pastikan gambar template kamu sudah diletakkan di folder ini dan dinamai '{TEMPLATE_PATH}'.")
        return

    if not os.path.exists(CSV_PATH):
        print(f"\n[ERROR] File '{CSV_PATH}' tidak ditemukan!")
        return

    ensure_fonts()
    
    # Load Font
    try:
        # Gunakan font sistem bawaan agar terlihat tebal dan proporsional (Helvetica/Arial untuk MacOS/Windows)
        font_path_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if os.path.exists("/System/Library/Fonts/Supplemental/Arial Bold.ttf") else "arialbd.ttf"
        font_path_reg = "/System/Library/Fonts/Supplemental/Arial.ttf" if os.path.exists("/System/Library/Fonts/Supplemental/Arial.ttf") else "arial.ttf"
        
        try:
            font_nama = ImageFont.truetype(font_path_bold, FONT_NAMA_SIZE)
        except:
            font_nama = ImageFont.load_default()
            
        try:
            font_topik = ImageFont.truetype(font_path_bold, FONT_TOPIK_SIZE)
        except:
            font_topik = ImageFont.load_default()

        try:
            font_tanggal = ImageFont.truetype(font_path_bold, FONT_TANGGAL_SIZE)
        except:
            font_tanggal = ImageFont.load_default()
            
        try:
            font_nomor = ImageFont.truetype(font_path_bold, FONT_NOMOR_SIZE) # Pake Bold
            font_subtitle = ImageFont.truetype(font_path_reg, 50) # Untuk teks "For actively participating..."
        except:
            font_nomor = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()
            
    except Exception as e:
        print(f"[WARNING] Gagal meload font: {e}")
        font_nama = ImageFont.load_default()
        font_topik = ImageFont.load_default()
        font_tanggal = ImageFont.load_default()
        font_nomor = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

    # Load CSV List Peserta
    df = pd.read_csv(CSV_PATH)
    
    # Load Template
    # Ubah format template menjadi RGBA dulu agar support tandatangan png transparan
    try:
        base_template = Image.open(TEMPLATE_PATH).convert("RGBA")
        template_width, template_height = base_template.size
        print(f"INFO: Ukuran gambar template kamu adalah: Lebar {template_width}px, Tinggi {template_height}px.")
        print("Jika nama peserta miring atau kurang pas letaknya, bisa sesuaikan nilai 'POS_NAMA' di dalam script generate.py.")
    except Exception as e:
        print(f"[ERROR] Gagal membuka template: {e}")
        return

    # Load Signature jika tersedia
    has_signature = False
    if os.path.exists(SIGNATURE_PATH):
        try:
            # Pastikan transparansi tidak hilang saat diload
            sign_img = Image.open(SIGNATURE_PATH).convert("RGBA")
            sign_img = sign_img.resize(SIGNATURE_RESIZE)
            has_signature = True
        except Exception as e:
            print(f"[WARNING] Gagal memuat tandatangan: {e}")
    else:
        print(f"\n[INFO] '{SIGNATURE_PATH}' tidak ditemukan. Sertifikat akan dibuat TANPA tandatangan. Jika ingin ditambahkan, letakkan gambar PNG tersebut.")

    print("\n-------------------------------------------")
    print("MEMULAI GENERATE SERTIFIKAT...")
    print("-------------------------------------------\n")

    # Siapkan counter otomatis untuk tiap sesi (supaya nggak usah manual input urutan lagi)
    counter_sesi = {"S1": 0, "S2": 0, "S3": 0}

    # Bikin 5 dulu buat ngetest biar penyimpanan Hard Disk macbook ngga kepenuhan lagi
    for index, row in df.head(5).iterrows():
        # Kolom di G-Form: Nama Lengkap
        nama = str(row.get('Nama Lengkap', '')).strip()
        
        # Kolom di G-Form: Sesi Webinar yang Diikuti (ada spasi di belakangnya di CSV)
        sesi_raw = str(row.get('Sesi Webinar yang Diikuti ', '')).strip()
        
        # Ekstrak Sesi berdasarkan teks
        if "Sesi 1" in sesi_raw:
            sesi = "S1"
        elif "Sesi 2" in sesi_raw:
            sesi = "S2"
        elif "Sesi 3" in sesi_raw:
            sesi = "S3"
        else:
            print(f"Melewati {nama} karena sesi tidak dikenali: {sesi_raw}")
            continue
            
        # Naikkan counter untuk sesi tersebut
        counter_sesi[sesi] += 1
        urutan = str(counter_sesi[sesi]).zfill(3)
        
        # Ambil data dari mapping config di atas
        sesi_info = SESSIONS.get(sesi, {})
        
        # Ekstrak data
        event_date_no = sesi_info.get("event_date_no", "00000000")
        cert_date     = sesi_info.get("cert_date", "")
        topik         = sesi_info.get("topic", "")
        
        # Buat format nomor sertifikat (contoh: REA/28022026/S1/073)
        no_sertifikat = f"REA/{event_date_no}/{sesi}/{urutan}"

        print(f"Memproses {index+1}/{len(df)}: [{no_sertifikat}] {nama}")

        # Gandakan base template agar kita punya kanvas yang fresh
        temp_image = Image.new("RGBA", (template_width, template_height))
        temp_image.paste(base_template, (0, 0))

        # 1. TEMPEL TANDATANGAN (Pastikan paste transparan menggunakan alpha channelnya sendiri)
        if has_signature:
            # Karena sign_img adalah RGBA, kita paste menggunakan mask=sign_img supaya transparan dipertahankan
            temp_image.paste(sign_img, POS_SIGNATURE, mask=sign_img)

        # Setup fitur "menulis" di gambar
        draw = ImageDraw.Draw(temp_image)

        # 2. TULIS NAMA
        draw.text(POS_NAMA, nama, font=font_nama, fill=FONT_NAMA_COLOR, anchor="mm")
        
        # 3. TULIS JUDUL TOPIK
        if topik:
            draw.text(POS_TOPIK, topik, font=font_topik, fill=FONT_TOPIK_COLOR, anchor="mm", align="center")
            
        # 4. TULIS TANGGAL
        if cert_date:
            draw.text(POS_TANGGAL, cert_date, font=font_tanggal, fill=FONT_TEXT_COLOR, anchor="mm")

        # 6. TULIS NOMOR SERTIFIKAT
        draw.text(POS_NOMOR, no_sertifikat, font=font_nomor, fill=FONT_NOMOR_COLOR, anchor="mm")

        # Save sebagai file JPG berkualitas tinggi (Ubah balek ke RGB)
        output_filename = os.path.join(OUTPUT_DIR, f"{no_sertifikat.replace('/', '-')} - {nama}.jpg")
        final_image = temp_image.convert("RGB")
        final_image.save(output_filename, quality=95)

    print("\n[SUKSES] Semua sertifikat telah berhasil dibuat di dalam folder 'output/'.")

if __name__ == "__main__":
    main()
