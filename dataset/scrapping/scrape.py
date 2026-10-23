import base64
import hashlib
import json
import os
import pandas as pd
try:
    from curl_cffi import requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests
    HAS_CURL_CFFI = False

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

# ============================================================
# KONFIGURASI API & ENKRIPSI KEMENDIKDASMEN
# ============================================================
SECRET_KEY = "KJ2HJ3LK45JH23K4JH5234H5234K5JH232K3J5KL"
BASE_URL = "https://tka.kemendikdasmen.go.id/hasiltka/hasil-api-2026/api/services/apps/"


def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    """Implementasi OpenSSL / CryptoJS EVP_BytesToKey untuk derivasi key & iv AES."""
    data = b""
    previous = b""
    while len(data) < key_len + iv_len:
        previous = hashlib.md5(previous + password + salt).digest()
        data += previous
    return data[:key_len], data[key_len:key_len + iv_len]


def decrypt_cryptojs(ciphertext, secret_key=SECRET_KEY):
    """Mendekripsi data respons dari API (CryptoJS AES-CBC)."""
    raw = base64.b64decode(ciphertext)
    assert raw[:8] == b"Salted__", "Format ciphertext bukan CryptoJS OpenSSL Salted__"
    salt = raw[8:16]
    encrypted = raw[16:]
    key, iv = evp_bytes_to_key(secret_key.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return decrypted.decode("utf-8")


def encrypt_cryptojs(plaintext, secret_key=SECRET_KEY):
    """Mengenkripsi payload request (CryptoJS AES-CBC)."""
    if not isinstance(plaintext, str):
        plaintext = json.dumps(plaintext)
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(secret_key.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(b"Salted__" + salt + encrypted).decode("utf-8")


def call_api(endpoint, payload=None):
    """Mengirim request POST terenkripsi ke API TKA Kemendikdasmen."""
    if payload is None:
        payload = {}
    url = f"{BASE_URL}{endpoint}"
    body = {
        "encrypted": True,
        "data": encrypt_cryptojs(payload)
    }
    kwargs = {"json": body, "timeout": 60}
    if HAS_CURL_CFFI:
        kwargs["impersonate"] = "chrome"
    else:
        kwargs["headers"] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    res = requests.post(url, **kwargs)
    if res.status_code != 200:
        raise Exception(f"API Error {res.status_code}: {res.text}")
    res_json = res.json()
    if res_json.get("encrypted"):
        decrypted_str = decrypt_cryptojs(res_json["data"])
        return json.loads(decrypted_str)
    return res_json.get("data")


def scrape_kabupaten(even_tka="smasmk", kd_prop="02", output_prefix=None, kd_jenjang="T", jenis_sek="T", label_jenjang=None):
    """
    Scraping nilai TKA tingkat Kabupaten/Kota.
    Parameter:
      - even_tka: 'sd', 'smp', atau 'smasmk'
      - kd_prop: '02' (Jawa Barat), atau '' (Nasional)
      - output_prefix: prefix path / nama file output CSV
      - kd_jenjang: 'T' (Semua), 'SMP', 'PAKETB', 'SLB', 'SD', 'SMA', 'SMK', dll.
      - jenis_sek:
          Untuk SMP: 'T' (Semua), '1' (SMP), '2' (MTs), '6' (SMPTK), '7' (MADYA WP)
          Untuk SD : 'T' (Semua), '1' (SD), '2' (MI), '4' (SDTK), '6' (ADI WP), '7' (Budha)
          Untuk SMA: 'T' (Semua), '1' (SMA), '2' (MA), '5' (SMAgK), dll.
      - label_jenjang: Label teks untuk kolom CSV (misal 'MTS', 'SMP', 'SD', dll.)
    """
    label_even = label_jenjang.upper() if label_jenjang else even_tka.upper()
    if output_prefix is None:
        prop_label = "jabar" if kd_prop == "02" else ("nasional" if kd_prop == "" else f"prop_{kd_prop}")
        output_prefix = f"tka_kabupaten_{prop_label}_{even_tka}"

    print("=" * 70)
    print(f"SCRAPING NILAI TKA KABUPATEN/KOTA - JENJANG: {label_even} (KD_PROP: '{kd_prop}')")
    print("=" * 70)

    # 1. Master Provinsi
    prov_res = call_api("listprovinsi")
    prov_map = {}
    for p in prov_res.get("data", []):
        kd = p.get("kd_prop")
        nm = p.get("nm_prop", "").strip()
        prov_map[kd] = f"{kd} - {nm}"

    # 2. Master Mata Pelajaran
    print(f"[1/3] Mengambil daftar mata pelajaran ({label_even})...")
    mapel_res = call_api("listmapel", {"even_tka": even_tka, "jenjang": ""})
    mapels = sorted(mapel_res.get("data", []), key=lambda x: x.get("urut", 0))
    print(f"      Ditemukan {len(mapels)} mata pelajaran:")
    for m in mapels:
        print(f"      - {m.get('urut')}. {m.get('mapel')} ({m.get('nama_field')})")

    # 3. Request Data Kabupaten/Kota
    print(f"[2/3] Mengambil data statistik kabupaten/kota ({label_even} - jenjang: {kd_jenjang}, jenis: {jenis_sek})...")
    payload = {
        "kd_prop": kd_prop,
        "kd_rayon": "",
        "even_tka": even_tka,
        "kd_jenjang": kd_jenjang,
        "jenis_sek": jenis_sek,
        "status_sek": "T",    # Negeri + Swasta
        "page": 1,
        "limit": 1000 if not kd_prop else 100
    }
    rayon_res = call_api("listdatatakrayon", payload)
    rows = rayon_res.get("data", [])
    print(f"      Berhasil menerima {len(rows)} data kabupaten/kota.")

    # 4. Parsing ke Format Long dan Wide
    print(f"[3/3] Menyusun data {label_even} ke CSV...")
    parsed_long = []
    parsed_wide = []

    for row in rows:
        prop_id = row.get("kode_provinsi", kd_prop)
        prop_name = prov_map.get(prop_id, f"{prop_id} - JAWA BARAT" if prop_id == "02" else f"PROVINSI {prop_id}")
        kode_rayon = row.get("kode_rayon", "")
        nama_rayon = row.get("nm_rayon", "").strip()

        wide_entry = {
            "provinsi": prop_name,
            "kode_kabupaten": kode_rayon,
            "kabupaten_kota": nama_rayon,
            "jenjang_tka": label_even
        }

        for m in mapels:
            urut = m.get("urut")
            field_name = m.get("nama_field")
            label_mapel = m.get("mapel")

            jml_sek = row.get(f"jml_sek_{field_name}")
            jml_pes = row.get(f"jml_pes_{field_name}")
            mean = row.get(f"mean_{field_name}")
            p10 = row.get(f"persen_10_{field_name}")
            med = row.get(f"median_{field_name}")
            p90 = row.get(f"persen_90_{field_name}")
            stdv = row.get(f"stdv_{field_name}")
            istimewa = row.get(f"istimewa_{field_name}")
            baik = row.get(f"baik_{field_name}")
            memadai = row.get(f"memadai_{field_name}")
            kurang = row.get(f"kurang_{field_name}")

            parsed_long.append({
                "provinsi": prop_name,
                "kode_kabupaten": kode_rayon,
                "kabupaten_kota": nama_rayon,
                "jenjang_tka": label_even,
                "no": urut,
                "mata_pelajaran": label_mapel,
                "jumlah_sekolah": jml_sek if jml_sek is not None else 0,
                "jumlah_siswa": jml_pes if jml_pes is not None else 0,
                "rerata": round(mean, 2) if mean is not None else None,
                "persentil_10": round(p10, 2) if p10 is not None else None,
                "median": round(med, 2) if med is not None else None,
                "persentil_90": round(p90, 2) if p90 is not None else None,
                "standar_deviasi": round(stdv, 2) if stdv is not None else None,
                "istimewa": round(istimewa, 2) if istimewa is not None else None,
                "baik": round(baik, 2) if baik is not None else None,
                "memadai": round(memadai, 2) if memadai is not None else None,
                "kurang": round(kurang, 2) if kurang is not None else None,
            })

            wide_entry[f"rerata_{label_mapel}"] = round(mean, 2) if mean is not None else None
            wide_entry[f"peserta_{label_mapel}"] = jml_pes if jml_pes is not None else 0

        parsed_wide.append(wide_entry)

    # Pastikan folder tujuan ada
    output_dir = os.path.dirname(output_prefix)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Simpan Long CSV
    df_long = pd.DataFrame(parsed_long)
    csv_long_file = f"{output_prefix}.csv"
    df_long.to_csv(csv_long_file, index=False)
    print(f"      [OK] Tersimpan: {csv_long_file} ({len(df_long)} baris)")

    # Simpan Wide CSV
    df_wide = pd.DataFrame(parsed_wide)
    csv_wide_file = f"{output_prefix}_wide.csv"
    df_wide.to_csv(csv_wide_file, index=False)
    print(f"      [OK] Tersimpan: {csv_wide_file} ({len(df_wide)} baris)")

    return df_long, df_wide


if __name__ == "__main__":
    tka_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "TKA"))

    # 1. Scraping SMP Saja - Jawa Barat (kd_jenjang="SMP", jenis_sek="1")
    scrape_kabupaten(
        even_tka="smp",
        kd_prop="02",
        kd_jenjang="SMP",
        jenis_sek="1",
        label_jenjang="SMP",
        output_prefix=os.path.join(tka_dir, "tka_kabupaten_jabar_smp")
    )

    # 2. Scraping MTs Saja - Jawa Barat (kd_jenjang="SMP", jenis_sek="2")
    scrape_kabupaten(
        even_tka="smp",
        kd_prop="02",
        kd_jenjang="SMP",
        jenis_sek="2",
        label_jenjang="MTS",
        output_prefix=os.path.join(tka_dir, "tka_kabupaten_jabar_mts")
    )

    print("\nScraping SMP dan MTs Jawa Barat berhasil disimpan di folder dataset/TKA!")