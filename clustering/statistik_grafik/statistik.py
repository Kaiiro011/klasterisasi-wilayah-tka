import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

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

# Variabel yang akan diperiksa
variabel = [
    "tka_rerata_bind",
    "tka_rerata_mtk",
    "rasio_murid_guru",
    "rasio_murid_sekolah",
    "pct_penduduk_miskin",
    "garis_kemiskinan_rp",
    "pct_tkp_s1_ke_atas",
]

# Statistik deskriptif
statistik = df[variabel].describe().T
statistik["median"] = df[variabel].median()
statistik = statistik[
    ["count", "mean", "median", "std", "min", "max"]
].round(2)

print(statistik)

# Simpan hasil statistik
statistik.to_csv(OUTPUT_DIR / "statistik_deskriptif.csv")

# 1. Histogram EDA
for kolom, judul in [
    ("tka_rerata_bind", "Distribusi Rerata TKA Bahasa Indonesia"),
    ("tka_rerata_mtk", "Distribusi Rerata TKA Matematika"),
]:
    plt.figure(figsize=(8, 5))
    plt.hist(df[kolom], bins=7, edgecolor="black")
    plt.title(judul)
    plt.xlabel("Nilai rerata")
    plt.ylabel("Jumlah kabupaten/kota")
    plt.tight_layout()
    plt.savefig(GRAFIK_DIR / f"{kolom}.png", dpi=150)
    plt.show()
    plt.close()

# Daftar pasangan kolom dan label
pasangan = [
    ("tka_rerata_bind", "TKA Bahasa Indonesia"),
    ("tka_rerata_mtk", "TKA Matematika"),
]

# 2. Perbandingan 10 wilayah terendah dan tertinggi
for kolom, judul in pasangan:
    urut = df.sort_values(kolom)

    pilihan = pd.concat([urut.head(10), urut.tail(10)])

    plt.figure(figsize=(10, 8))
    plt.barh(pilihan["nama_pendek"], pilihan[kolom])
    plt.xlabel(f"Rerata {judul}")
    plt.ylabel("Kabupaten/kota")
    plt.title(f"Perbandingan 10 Wilayah Terendah dan Tertinggi ({judul})")
    plt.tight_layout()

    # Perbaikan sintaks penamaan file
    plt.savefig(GRAFIK_DIR / f"perbandingan_{kolom}.png", dpi=150)
    plt.show()
    plt.close()

# 3. Scatter Plot TKA vs Kemiskinan
for kolom, judul in pasangan:
    plt.figure(figsize=(8, 5))

    plt.scatter(df["pct_penduduk_miskin"], df[kolom])

    for _, baris in df.iterrows():
        plt.annotate(
            baris["nama_pendek"],
            (baris["pct_penduduk_miskin"], baris[kolom]),
            fontsize=7,
            xytext=(3, 3),
            textcoords="offset points",
        )

    plt.xlabel("Penduduk miskin (%)")
    plt.ylabel(f"Rerata {judul}")
    plt.title(f"{judul} vs Persentase Penduduk Miskin")
    plt.tight_layout()

    plt.savefig(GRAFIK_DIR / f"{kolom}_vs_kemiskinan.png", dpi=150)
    plt.show()
    plt.close()