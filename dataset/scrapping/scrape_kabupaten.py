import base64
import hashlib
import json
import os
import pandas as pd
from curl_cffi import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad

SECRET_KEY = "KJ2HJ3LK45JH23K4JH5234H5234K5JH232K3J5KL"
BASE_URL = "https://tka.kemendikdasmen.go.id/hasiltka/hasil-api-2026/api/services/apps/"

def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
    data = b""
    previous = b""
    while len(data) < key_len + iv_len:
        previous = hashlib.md5(previous + password + salt).digest()
        data += previous
    return data[:key_len], data[key_len:key_len + iv_len]

def decrypt_cryptojs(ciphertext, secret_key=SECRET_KEY):
    raw = base64.b64decode(ciphertext)
    assert raw[:8] == b"Salted__"
    salt = raw[8:16]
    encrypted = raw[16:]
    key, iv = evp_bytes_to_key(secret_key.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return decrypted.decode("utf-8")

def encrypt_cryptojs(plaintext, secret_key=SECRET_KEY):
    if not isinstance(plaintext, str):
        plaintext = json.dumps(plaintext)
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(secret_key.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(b"Salted__" + salt + encrypted).decode("utf-8")

def call_api(endpoint, payload=None):
    if payload is None:
        payload = {}
    url = f"{BASE_URL}{endpoint}"
    body = {
        "encrypted": True,
        "data": encrypt_cryptojs(payload)
    }
    res = requests.post(url, json=body, impersonate="chrome", timeout=60)
    if res.status_code != 200:
        raise Exception(f"API Error {res.status_code}: {res.text}")
    res_json = res.json()
    if res_json.get("encrypted"):
        decrypted_str = decrypt_cryptojs(res_json["data"])
        return json.loads(decrypted_str)
    return res_json.get("data")

def main():
    print("=" * 60)
    print("SCRAPER TKA TINGKAT KABUPATEN/KOTA (JAWA BARAT & NASIONAL)")
    print("=" * 60)

    # 1. Ambil Master Provinsi
    print("[1/5] Mengambil data provinsi...")
    prov_res = call_api("listprovinsi")
    prov_map = {}
    for p in prov_res.get("data", []):
        kd = p.get("kd_prop")
        nm = p.get("nm_prop", "").strip()
        prov_map[kd] = f"{kd} - {nm}"
    print(f"      Ditemukan {len(prov_map)} provinsi.")

    # 2. Ambil Master Mapel
    print("[2/5] Mengambil data mata pelajaran...")
    mapel_res = call_api("listmapel", {"even_tka": "smasmk", "jenjang": ""})
    mapels = sorted(mapel_res.get("data", []), key=lambda x: x.get("urut", 0))
    print(f"      Ditemukan {len(mapels)} mata pelajaran.")
    for m in mapels:
        print(f"      - {m.get('urut')}. {m.get('mapel')} ({m.get('nama_field')})")

    # 3. Ambil data TKA Kabupaten/Kota Jawa Barat (kd_prop = '02')
    print("\n[3/5] Mengambil data TKA Kabupaten & Kota di JAWA BARAT...")
    payload_jabar = {
        "kd_prop": "02",
        "kd_rayon": "",
        "even_tka": "smasmk",
        "kd_jenjang": "T",
        "jenis_sek": "T",
        "status_sek": "T",
        "page": 1,
        "limit": 100
    }
    jabar_res = call_api("listdatatakrayon", payload_jabar)
    jabar_rows = jabar_res.get("data", [])
    print(f"      Berhasil mendapatkan {len(jabar_rows)} Kabupaten/Kota di Jawa Barat.")

    # Parse rows into standard format (long format)
    parsed_jabar_long = []
    parsed_jabar_wide = []

    for row in jabar_rows:
        kd_prop = row.get("kode_provinsi", "02")
        nm_prop = prov_map.get(kd_prop, "02 - JAWA BARAT")
        kd_rayon = row.get("kode_rayon", "")
        nm_rayon = row.get("nm_rayon", "").strip()

        wide_item = {
            "provinsi": nm_prop,
            "kode_kabupaten": kd_rayon,
            "kabupaten_kota": nm_rayon
        }

        for m in mapels:
            urut = m.get("urut")
            field_name = m.get("nama_field")
            label_mapel = m.get("mapel")

            # Extract metrics
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

            parsed_jabar_long.append({
                "provinsi": nm_prop,
                "kode_kabupaten": kd_rayon,
                "kabupaten_kota": nm_rayon,
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

            wide_item[f"rerata_{label_mapel}"] = round(mean, 2) if mean is not None else None
            wide_item[f"peserta_{label_mapel}"] = jml_pes if jml_pes is not None else 0

        parsed_jabar_wide.append(wide_item)

    # 4. Simpan CSV Jawa Barat
    print("\n[4/5] Menyimpan dataset Jawa Barat...")
    df_jabar_long = pd.DataFrame(parsed_jabar_long)
    df_jabar_long.to_csv("tka_kabupaten_jabar.csv", index=False)
    print(f"      Saved: tka_kabupaten_jabar.csv ({len(df_jabar_long)} baris)")

    df_jabar_wide = pd.DataFrame(parsed_jabar_wide)
    df_jabar_wide.to_csv("tka_kabupaten_jabar_wide.csv", index=False)
    print(f"      Saved: tka_kabupaten_jabar_wide.csv ({len(df_jabar_wide)} baris)")

    # 5. Ambil data SELURUH KABUPATEN/KOTA SE-INDONESIA (Nasional)
    print("\n[5/5] Mengambil data TKA Kabupaten/Kota SELURUH INDONESIA (522 kab/kota)...")
    payload_nasional = {
        "kd_prop": "",
        "kd_rayon": "",
        "even_tka": "smasmk",
        "kd_jenjang": "T",
        "jenis_sek": "T",
        "status_sek": "T",
        "page": 1,
        "limit": 1000
    }
    nasional_res = call_api("listdatatakrayon", payload_nasional)
    nasional_rows = nasional_res.get("data", [])
    print(f"      Berhasil mendapatkan {len(nasional_rows)} Kabupaten/Kota se-Indonesia.")

    parsed_nasional_long = []
    for row in nasional_rows:
        kd_prop = row.get("kode_provinsi", "")
        nm_prop = prov_map.get(kd_prop, f"{kd_prop} - PROVINSI {kd_prop}")
        kd_rayon = row.get("kode_rayon", "")
        nm_rayon = row.get("nm_rayon", "").strip()

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

            parsed_nasional_long.append({
                "provinsi": nm_prop,
                "kode_kabupaten": kd_rayon,
                "kabupaten_kota": nm_rayon,
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

    df_nasional_long = pd.DataFrame(parsed_nasional_long)
    df_nasional_long.to_csv("tka_kabupaten_nasional.csv", index=False)
    print(f"      Saved: tka_kabupaten_nasional.csv ({len(df_nasional_long)} baris)")

    print("\n" + "=" * 60)
    print("SELESAI! Semua file CSV berhasil dibuat dengan lengkap.")
    print("=" * 60)

if __name__ == "__main__":
    main()
