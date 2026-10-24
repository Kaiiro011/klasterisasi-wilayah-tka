import pandas as pd
from sklearn.preprocessing import StandardScaler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "dataset" / "fitur_kandidat_kmeans_smp.csv"

# 1. Baca dataset
df = pd.read_csv(DATA_PATH)

# 2. Pilih lima fitur klasterisasi
fitur = [
    "tka_rerata_mtk",
    "tka_rerata_bind",
    "rasio_murid_guru",
    "rasio_murid_sekolah",
    "pct_penduduk_miskin"
]

# 3. Pastikan semua fitur berbentuk numerik
df[fitur] = df[fitur].apply(pd.to_numeric, errors="coerce")

# 4. Periksa data kosong
if df[fitur].isnull().any().any():
    raise ValueError(
        "Ada nilai kosong atau nonnumerik pada fitur. "
        "Periksa dan tangani sebelum standardisasi."
    )

# 5. Standardisasi dengan Z-score
scaler = StandardScaler()
data_standar = scaler.fit_transform(df[fitur])

# 6. Simpan hasil standardisasi
df_standar = pd.DataFrame(
    data_standar,
    columns=fitur,
    index=df.index
)

# 7. Simpan identitas wilayah dan fitur standar
kolom_identitas = [
    kolom for kolom in
    ["kode_wilayah", "kode_bps", "nama_kabkota", "nama_pendek"]
    if kolom in df.columns
]

hasil = pd.concat(
    [df[kolom_identitas], df_standar],
    axis=1
)

hasil.to_csv(
    BASE_DIR / "dataset" / "fitur_kmeans_smp_standardisasi.csv",
    index=False
)

print("Standardisasi selesai!")
print(hasil.head())
print("\nRata-rata fitur standar:")
print(df_standar.mean().round(4))
print("\nStandar deviasi fitur standar:")
print(df_standar.std(ddof=0).round(4))