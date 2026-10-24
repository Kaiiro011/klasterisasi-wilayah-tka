import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

# 1. Tentukan path file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "dataset" / "fitur_kmeans_smp_standardisasi.csv"
OUTPUT_DIR = BASE_DIR / "clustering" / "statistik_grafik"
GRAFIK_DIR = OUTPUT_DIR / "grafik_eda"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAFIK_DIR.mkdir(parents=True, exist_ok=True)

# 2. Baca dataset hasil standardisasi
df = pd.read_csv(DATA_PATH)

fitur = [
    "tka_rerata_mtk",
    "tka_rerata_bind",
    "rasio_murid_guru",
    "rasio_murid_sekolah",
    "pct_penduduk_miskin"
]

X = df[fitur].values

# 3. Uji nilai k dari 2 sampai 8
k_range = range(2, 9)
hasil_evaluasi = []

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    inertia = kmeans.inertia_
    sil = silhouette_score(X, labels)
    dbi = davies_bouldin_score(X, labels)
    ch = calinski_harabasz_score(X, labels)
    
    hasil_evaluasi.append({
        "k": k,
        "inertia_wcss": round(inertia, 4),
        "silhouette_score": round(sil, 4),
        "davies_bouldin_index": round(dbi, 4),
        "calinski_harabasz": round(ch, 4)
    })

df_eval = pd.DataFrame(hasil_evaluasi)

# Simpan tabel hasil evaluasi
csv_output = OUTPUT_DIR / "evaluasi_optimal_k.csv"
df_eval.to_csv(csv_output, index=False)
print("=== TABEL EVALUASI JUMLAH KLASTER (k) ===")
print(df_eval.to_string(index=False))

# 4. Buat Grafik Perbandingan Metrik
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Elbow Method (Inertia/WCSS)
axes[0].plot(df_eval["k"], df_eval["inertia_wcss"], marker="o", color="#2563eb", linewidth=2, markersize=7)
axes[0].set_title("Elbow Method (Inertia / WCSS)\n(Cari titik siku/penurunan melandai)", fontsize=11, fontweight="bold")
axes[0].set_xlabel("Jumlah Klaster (k)")
axes[0].set_ylabel("Inertia (WCSS)")
axes[0].grid(True, linestyle="--", alpha=0.6)
axes[0].set_xticks(list(k_range))

# Plot 2: Silhouette Score
axes[1].plot(df_eval["k"], df_eval["silhouette_score"], marker="s", color="#16a34a", linewidth=2, markersize=7)
axes[1].set_title("Silhouette Score\n(Semakin tinggi semakin baik)", fontsize=11, fontweight="bold")
axes[1].set_xlabel("Jumlah Klaster (k)")
axes[1].set_ylabel("Silhouette Score")
axes[1].grid(True, linestyle="--", alpha=0.6)
axes[1].set_xticks(list(k_range))

# Plot 3: Davies-Bouldin Index
axes[2].plot(df_eval["k"], df_eval["davies_bouldin_index"], marker="^", color="#dc2626", linewidth=2, markersize=7)
axes[2].set_title("Davies-Bouldin Index\n(Semakin rendah semakin baik)", fontsize=11, fontweight="bold")
axes[2].set_xlabel("Jumlah Klaster (k)")
axes[2].set_ylabel("Davies-Bouldin Index")
axes[2].grid(True, linestyle="--", alpha=0.6)
axes[2].set_xticks(list(k_range))

plt.suptitle("Evaluasi Penentuan Nilai Optimal k (K-Means Clustering SMP Jabar)", fontsize=14, fontweight="bold", y=1.03)
plt.tight_layout()

# Simpan grafik
grafik_path = GRAFIK_DIR / "evaluasi_optimal_k.png"
plt.savefig(grafik_path, dpi=200, bbox_inches="tight")
plt.close()

print(f"\nGrafik evaluasi berhasil disimpan di: {grafik_path}")
print(f"Data evaluasi berhasil disimpan di: {csv_output}")
