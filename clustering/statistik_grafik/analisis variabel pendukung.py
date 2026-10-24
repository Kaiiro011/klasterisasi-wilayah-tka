# 8. Analisis Hubungan Capaian TKA dengan Variabel Pendukung
from scipy import stats

target = "tka_rerata_mtk"
pendukung = ["rasio_murid_guru", "rasio_murid_sekolah", "pct_penduduk_miskin"]
label_pendukung = {
    "rasio_murid_guru": "Rasio Murid/Guru",
    "rasio_murid_sekolah": "Rasio Murid/Sekolah",
    "pct_penduduk_miskin": "Persentase Penduduk Miskin (%)"
}

# 8a. Korelasi Pearson & Spearman + uji signifikansi
baris = []
for v in pendukung:
    r_p, p_p = stats.pearsonr(hasil_df[v], hasil_df[target])
    r_s, p_s = stats.spearmanr(hasil_df[v], hasil_df[target])
    slope, intercept, r_val, p_reg, se = stats.linregress(hasil_df[v], hasil_df[target])
    baris.append({
        "variabel": v,
        "pearson_r": round(r_p, 3), "pearson_p": round(p_p, 4),
        "spearman_rho": round(r_s, 3), "spearman_p": round(p_s, 4),
        "slope": round(slope, 4), "r_kuadrat": round(r_val ** 2, 3),
    })

korelasi_df = pd.DataFrame(baris)
korelasi_csv = OUTPUT_DIR / "korelasi_tka_variabel_pendukung.csv"
korelasi_df.to_csv(korelasi_csv, index=False)
print("\n=== KORELASI TKA MATEMATIKA DENGAN VARIABEL PENDUKUNG ===")
print(korelasi_df.to_string(index=False))

# 8b. Matriks korelasi seluruh fitur (heatmap)
corr = hasil_df[fitur].corr(method="pearson")
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(fitur)))
ax.set_yticks(range(len(fitur)))
ax.set_xticklabels(fitur_labels, rotation=30, ha="right")
ax.set_yticklabels(fitur_labels)
for i in range(len(fitur)):
    for j in range(len(fitur)):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=10, fontweight="bold")
plt.colorbar(im, ax=ax, label="Koefisien Korelasi Pearson")
ax.set_title("Matriks Korelasi Antar-Fitur", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(GRAFIK_DIR / "heatmap_korelasi.png", dpi=200, bbox_inches="tight")
plt.close()

# 8c. Scatter plot + garis regresi per variabel pendukung
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
for ax, v in zip(axes, pendukung):
    for nama_klaster, grup in hasil_df.groupby("nama_klaster_k3"):
        ax.scatter(grup[v], grup[target], color=warna_klaster.get(nama_klaster, "gray"),
                   s=70, alpha=0.85, edgecolors="black", label=nama_klaster)
    slope, intercept, r_val, p_reg, _ = stats.linregress(hasil_df[v], hasil_df[target])
    xs = np.linspace(hasil_df[v].min(), hasil_df[v].max(), 100)
    ax.plot(xs, slope * xs + intercept, color="black", linestyle="--", linewidth=1.5)
    ax.set_title(f"TKA MTK vs {label_pendukung[v]}\nr = {r_val:.2f}, p = {p_reg:.3f}",
                 fontsize=10, fontweight="bold")
    ax.set_xlabel(label_pendukung[v])
    ax.set_ylabel("Rerata TKA Matematika")
    ax.grid(True, linestyle="--", alpha=0.5)
axes[0].legend(fontsize=7, loc="best")
plt.suptitle("Hubungan Capaian TKA Matematika dengan Variabel Pendukung", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(GRAFIK_DIR / "scatter_regresi_tka.png", dpi=200, bbox_inches="tight")
plt.close()

# 8d. Perbedaan TKA antar-klaster (ANOVA satu arah + Kruskal-Wallis)
kelompok = [g[target].values for _, g in hasil_df.groupby("nama_klaster_k3")]
f_stat, p_anova = stats.f_oneway(*kelompok)
h_stat, p_kw = stats.kruskal(*kelompok)
print("\n=== UJI PERBEDAAN TKA MTK ANTAR-KLASTER ===")
print(f"ANOVA         : F = {f_stat:.3f}, p = {p_anova:.4f}")
print(f"Kruskal-Wallis: H = {h_stat:.3f}, p = {p_kw:.4f}")

# 8e. Boxplot TKA per klaster
fig, ax = plt.subplots(figsize=(8, 6))
nama_urut = list(label_mapping.values())
data_box = [hasil_df.loc[hasil_df["nama_klaster_k3"] == n, target] for n in nama_urut]
bp = ax.boxplot(data_box, patch_artist=True, tick_labels=["Wilayah\nMaju", "Darurat\nSarpras", "Rentan &\nTerpencil"])
for patch, n in zip(bp["boxes"], nama_urut):
    patch.set_facecolor(warna_klaster[n])
    patch.set_alpha(0.7)
ax.set_ylabel("Rerata TKA Matematika")
ax.set_title("Sebaran TKA Matematika per Klaster", fontsize=12, fontweight="bold")
ax.grid(True, linestyle="--", alpha=0.5, axis="y")
plt.tight_layout()
plt.savefig(GRAFIK_DIR / "boxplot_tka_per_klaster.png", dpi=200, bbox_inches="tight")
plt.close()

print(f"\nAnalisis hubungan TKA selesai. Output tersimpan di: {OUTPUT_DIR}")