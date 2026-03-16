from PIL import Image

def clean_template():
    img_path = 'assets/Sertifikat Webinar KODING KURMA_Sertifikat Peserta_2.jpg'
    output_path = 'assets/template_clean.jpg'
    
    print("Membaca gambar asli...")
    try:
        img = Image.open(img_path)
    except Exception as e:
        print(f"Gagal membaca gambar: {e}")
        return

    # Kita akan meng-kopi sebuah 'patch' kosong 
    # di sisi kiri gambar (misal di X=300 sampe 700) yang bersih dari teks,
    # lalu kita tempelkan (paste) menutupi teks lama (judul topik & tanggal).
    
    # Area Y (Tinggi) teks judul dan tanggal kira-kira di 1250 sampai 1750
    # Kita ambil patch dari X=700 ke X=900 karena X=300 sebelumnya mengenai gambar mandala di pinggir
    y_start, y_end = 1250, 1800
    patch_width = 200
    patch = img.crop((700, y_start, 700 + patch_width, y_end))
    
    print("Memanipulasi dan menghapus teks lama (menambal background)...")
    # Paste patch tersebut berulang ke kanan menimpa teks lama
    for x_pos in range(900, 2700, patch_width):
        img.paste(patch, (x_pos, y_start))
        
    print(f"Menyimpan template bersih ke '{output_path}'...")
    img.save(output_path, quality=95)
    print("SELESAI! Kamu sekarang punya 'template_clean.jpg'.")

if __name__ == "__main__":
    clean_template()
