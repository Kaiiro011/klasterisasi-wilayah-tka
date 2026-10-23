from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Menentukan direktori utama proyek (tka-clustering)
BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "dataset" / "jabar_smp_merged.csv"
OUTPUT_DIR = BASE_DIR / "clustering" / "statistik_grafik"
GRAFIK_DIR = BASE_DIR / "clustering" / "statistik_grafik" / "grafik_eda"

# Buat folder jika belum ada
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAFIK_DIR.mkdir(parents=True, exist_ok=True)

# Baca dataset
df = pd.read_csv(DATA_PATH)

# Pilih variabel numerik yang relevan untuk diperiksa
fitur_korelasi = [
    "sekolah_total",
    "guru_total",
    "murid_total",
    "rasio_murid_guru",
    "rasio_murid_sekolah",
    "tka_rerata_bind",
    "tka_rerata_mtk",
    "garis_kemiskinan_rp",
    "penduduk_miskin_ribu",
    "pct_penduduk_miskin",
    "tkp_total",
    "tkp_s1_ke_atas",
    "pct_tkp_s1_ke_atas",
    "guru_per_tkp",
]

corr = df[fitur_korelasi].corr()

# Buat heatmap tanpa seaborn
fig, ax = plt.subplots(figsize=(12, 10))

im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

ax.set_xticks(range(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=90)
ax.set_yticks(range(len(corr.columns)))
ax.set_yticklabels(corr.columns)

for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        ax.text(
            j,
            i,
            f"{corr.iloc[i, j]:.2f}",
            ha="center",
            va="center",
            fontsize=7,
        )

fig.colorbar(im, ax=ax, label="Koefisien Korelasi")
ax.set_title("Matriks Korelasi Variabel SMP Jawa Barat")
plt.tight_layout()

# Perbaikan: Hapus prefix 'grafik_eda/' karena sudah ada dalam GRAFIK_DIR
plt.savefig(GRAFIK_DIR / "matriks_korelasi.png", dpi=150)
plt.show()

# Simpan matriks korelasi ke OUTPUT_DIR
corr.to_csv(OUTPUT_DIR / "matriks_korelasi.csv")

# Ambil hanya segitiga atas agar pasangan tidak berulang
upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

pasangan_tinggi = upper.stack().reset_index()

pasangan_tinggi.columns = ["variabel_1", "variabel_2", "korelasi"]

pasangan_tinggi["abs_korelasi"] = pasangan_tinggi["korelasi"].abs()

pasangan_tinggi = pasangan_tinggi[
    pasangan_tinggi["abs_korelasi"] >= 0.85
].sort_values("abs_korelasi", ascending=False)

print(pasangan_tinggi.to_string(index=False))

# Simpan pasangan korelasi tinggi ke OUTPUT_DIR
pasangan_tinggi.to_csv(
    OUTPUT_DIR / "pasangan_korelasi_tinggi.csv", index=False
)