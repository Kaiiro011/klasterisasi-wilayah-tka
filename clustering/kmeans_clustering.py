import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.cluster import KMeans

# 1. Konfigurasi direktori
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_STD_PATH = BASE_DIR / "dataset" / "fitur_kmeans_smp_standardisasi.csv"
DATA_RAW_PATH = BASE_DIR / "dataset" / "fitur_kandidat_kmeans_smp.csv"
OUTPUT_DIR = BASE_DIR / "clustering" / "statistik_grafik"
GRAFIK_DIR = OUTPUT_DIR / "grafik_eda"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAFIK_DIR.mkdir(parents=True, exist_ok=True)

# 2. Muat data
df_std = pd.read_csv(DATA_STD_PATH)
df_raw = pd.read_csv(DATA_RAW_PATH)

fitur = [
    "tka_rerata_mtk",
    "tka_rerata_bind",
    "rasio_murid_guru",
    "rasio_murid_sekolah",
    "pct_penduduk_miskin"
]

X = df_std[fitur].values

# 3. Fitting K-Means dengan k=3 (Utama)
kmeans_3 = KMeans(n_clusters=3, random_state=42, n_init=10)
labels_k3 = kmeans_3.fit_predict(X)

# Fitting K-Means dengan k=4 (Pembanding)
kmeans_4 = KMeans(n_clusters=4, random_state=42, n_init=10)
labels_k4 = kmeans_4.fit_predict(X)

# 4. Tentukan Label Deskriptif untuk k=3
# Cari karakteristik masing-masing klaster berdasarkan nilai rata-rata
temp_df = df_raw.copy()
temp_df["temp_cluster"] = labels_k3
mean_stats = temp_df.groupby("temp_cluster")[fitur].mean()

label_mapping = {}
for c_id, row in mean_stats.iterrows():
    if row["tka_rerata_mtk"] > 42.0:
        label_mapping[c_id] = "Klaster 1: Wilayah Maju"
    elif row["rasio_murid_guru"] > 20.0:
        label_mapping[c_id] = "Klaster 2: Wilayah Darurat Sarana Prasarana"
    else:
        label_mapping[c_id] = "Klaster 3: Wilayah Rentan dan Terpencil"

# 5. Gabungkan Hasil Klasterisasi ke Dataset Final
hasil_df = df_raw.copy()
hasil_df["klaster_k3"] = labels_k3
hasil_df["nama_klaster_k3"] = hasil_df["klaster_k3"].map(label_mapping)
hasil_df["klaster_k4"] = labels_k4

# Simpan dataset hasil klasterisasi
output_csv = BASE_DIR / "dataset" / "hasil_klaster_kmeans_smp.csv"
hasil_df.to_csv(output_csv, index=False)
print(f"Dataset hasil klasterisasi berhasil disimpan di: {output_csv}")

# 6. Hitung Profiling Statistik Tiap Klaster (Nilai Asli)
profil_mean = hasil_df.groupby("nama_klaster_k3")[fitur].mean().round(2)
profil_std = hasil_df.groupby("nama_klaster_k3")[fitur].std().round(2)
profil_count = hasil_df.groupby("nama_klaster_k3")["nama_kabkota"].count().rename("jumlah_wilayah")

profil_ringkas = pd.concat([profil_count, profil_mean], axis=1).reset_index()
profil_csv = OUTPUT_DIR / "profil_klaster_smp.csv"
profil_ringkas.to_csv(profil_csv, index=False)
print("\n=== PROFIL STATISTIK RATA-RATA NILAI ASLI PER KLASTER ===")
print(profil_ringkas.to_string(index=False))

# Tampilkan anggota tiap klaster
print("\n=== ANGGOTA KABUPATEN/KOTA PER KLASTER ===")
for nama_klaster, grup in hasil_df.groupby("nama_klaster_k3"):
    print(f"\n[{nama_klaster}] (Total: {len(grup)} daerah)")
    print(", ".join(grup["nama_pendek"].tolist()))

# 7. Visualisasi Hasil Klasterisasi
fig, axes = plt.subplots(2, 2, figsize=(16, 13))

warna_klaster = {
    "Klaster 1: Wilayah Maju": "#2563eb",                      # Biru (Maju/Stabil)
    "Klaster 2: Wilayah Darurat Sarana Prasarana": "#f59e0b",   # Amber / Oranye (Peringatan Sarpras)
    "Klaster 3: Wilayah Rentan dan Terpencil": "#dc2626"       # Merah (Prioritas Afirmasi)
}

# Subplot 1: TKA MTK vs Persentase Kemiskinan
ax1 = axes[0, 0]
for nama_klaster, grup in hasil_df.groupby("nama_klaster_k3"):
    warna = warna_klaster.get(nama_klaster, "gray")
    ax1.scatter(grup["pct_penduduk_miskin"], grup["tka_rerata_mtk"], label=nama_klaster, color=warna, s=80, alpha=0.85, edgecolors="black")
    for _, r in grup.iterrows():
        ax1.annotate(r["nama_pendek"], (r["pct_penduduk_miskin"], r["tka_rerata_mtk"]), fontsize=8, xytext=(4, 4), textcoords="offset points")

ax1.set_title("Capaian TKA Matematika vs Persentase Kemiskinan", fontsize=11, fontweight="bold")
ax1.set_xlabel("Persentase Penduduk Miskin (%)")
ax1.set_ylabel("Rerata TKA Matematika")
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(loc="upper right", fontsize=8)

# Subplot 2: Rasio Murid/Guru vs Rasio Murid/Sekolah
ax2 = axes[0, 1]
for nama_klaster, grup in hasil_df.groupby("nama_klaster_k3"):
    warna = warna_klaster.get(nama_klaster, "gray")
    ax2.scatter(grup["rasio_murid_sekolah"], grup["rasio_murid_guru"], label=nama_klaster, color=warna, s=80, alpha=0.85, edgecolors="black")
    for _, r in grup.iterrows():
        ax2.annotate(r["nama_pendek"], (r["rasio_murid_sekolah"], r["rasio_murid_guru"]), fontsize=8, xytext=(4, 4), textcoords="offset points")

ax2.set_title("Rasio Murid/Guru vs Rasio Murid/Sekolah", fontsize=11, fontweight="bold")
ax2.set_xlabel("Rasio Murid per Sekolah")
ax2.set_ylabel("Rasio Murid per Guru")
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.legend(loc="upper left", fontsize=8)

# Subplot 3: Bar Chart Perbandingan Z-Score Centroid Antar-Klaster
ax3 = axes[1, 0]
df_std_labeled = df_std.copy()
df_std_labeled["nama_klaster_k3"] = hasil_df["nama_klaster_k3"]
centroid_z = df_std_labeled.groupby("nama_klaster_k3")[fitur].mean().T

posisi = np.arange(len(fitur))
lebar = 0.25
fitur_labels = ["TKA MTK", "TKA B.Ind", "Rasio M/G", "Rasio M/S", "Pmiskin (%)"]

for idx, (nama_klaster, nilai) in enumerate(centroid_z.items()):
    warna = warna_klaster.get(nama_klaster, "gray")
    ax3.bar(posisi + (idx - 1) * lebar, nilai, width=lebar, label=nama_klaster, color=warna, alpha=0.85, edgecolor="black")

ax3.axhline(0, color="black", linestyle="--", linewidth=0.8)
ax3.set_xticks(posisi)
ax3.set_xticklabels(fitur_labels, fontsize=9, fontweight="bold")
ax3.set_title("Karakteristik Z-Score Rata-Rata Antar-Klaster (Fingerprint)", fontsize=11, fontweight="bold")
ax3.set_ylabel("Rata-rata Z-Score")
ax3.grid(True, linestyle="--", alpha=0.5)
ax3.legend(loc="upper right", fontsize=8)

# Subplot 4: Distribusi Jumlah Wilayah per Klaster
ax4 = axes[1, 1]
klaster_names = profil_ringkas["nama_klaster_k3"].tolist()
klaster_counts = profil_ringkas["jumlah_wilayah"].tolist()
bar_colors = [warna_klaster.get(name, "gray") for name in klaster_names]

bars = ax4.bar(range(len(klaster_names)), klaster_counts, color=bar_colors, width=0.55, edgecolor="black")
ax4.set_xticks(range(len(klaster_names)))
short_labels = ["Wilayah\nMaju", "Darurat\nSarpras", "Rentan &\nTerpencil"]
ax4.set_xticklabels(short_labels, fontsize=9, fontweight="bold")
ax4.set_title("Distribusi Jumlah Kabupaten/Kota per Klaster (N=27)", fontsize=11, fontweight="bold")
ax4.set_ylabel("Jumlah Kabupaten/Kota")
ax4.set_ylim(0, max(klaster_counts) + 4)
ax4.grid(True, linestyle="--", alpha=0.5, axis="y")

for bar in bars:
    yval = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width() / 2, yval + 0.4, f"{int(yval)} daerah", ha="center", va="bottom", fontweight="bold", fontsize=10)

plt.suptitle("Hasil Klasterisasi Wilayah SMP Jawa Barat (K-Means, k=3)", fontsize=14, fontweight="bold", y=0.99)
plt.tight_layout()

# Simpan visualisasi
grafik_output = GRAFIK_DIR / "visualisasi_klaster_kmeans.png"
plt.savefig(grafik_output, dpi=200, bbox_inches="tight")
plt.close()

print(f"\nGrafik visualisasi klasterisasi berhasil disimpan di: {grafik_output}")
