from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd
import time
import re


# ============================================================
# KONFIGURASI
# ============================================================

URL = "https://tka.kemendikdasmen.go.id/hasiltka/"

OUTPUT = "tka_provinsi.csv"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 30)


# ============================================================
# DAFTAR MATA PELAJARAN
# ============================================================

subjects = {
    1: "Bahasa Indonesia",
    2: "Matematika",
    3: "Bahasa Inggris",
    4: "PPKn",
    5: "Antropologi",
    6: "Projek Kreatif dan Kewirausahaan",
    7: "Bahasa Indonesia Lanjut",
    8: "Matematika Lanjut",
    9: "Bahasa Inggris Lanjut",
    10: "Biologi",
    11: "Sosiologi",
    12: "Ekonomi",
    13: "Kimia",
    14: "Sejarah",
    15: "Fisika",
    16: "Geografi",
    17: "Bahasa Arab",
    18: "Bahasa Jepang",
    19: "Bahasa Mandarin",
    20: "Bahasa Jerman",
    21: "Bahasa Korea",
    22: "Bahasa Prancis",
}


# ============================================================
# AMBIL ROW DARI DOM
# ============================================================

def get_rows():

    selectors = [
        "table tbody tr",
        "[role='row']",
        ".ant-table-tbody > tr",
        ".MuiDataGrid-row",
        "tbody tr"
    ]

    for selector in selectors:

        rows = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        if len(rows) > 0:
            return rows

    return []


# ============================================================
# PARSE ANGKA
# ============================================================

def clean_number(value):

    value = value.strip()

    # Hilangkan %
    value = value.replace("%", "")

    # Hilangkan pemisah ribuan
    value = value.replace(",", "")

    return value


# ============================================================
# AMBIL STATISTIK MAPEL
# ============================================================

def ambil_statistik_mapel(nama_provinsi):

    print("Mencari tabel statistik...")

    # --------------------------------------------------------
    # Tunggu sampai row muncul
    # --------------------------------------------------------

    try:

        wait.until(
            lambda d: len(get_rows()) >= 20
        )

    except TimeoutException:

        print("Timeout menunggu row tabel.")

        return []


    time.sleep(1)


    # --------------------------------------------------------
    # Ambil semua row
    # --------------------------------------------------------

    rows = get_rows()

    print(
        "Jumlah row DOM:",
        len(rows)
    )


    hasil = []


    # --------------------------------------------------------
    # LOOP ROW
    # --------------------------------------------------------

    for index, row in enumerate(rows):

        text = row.text.strip()

        if not text:
            continue


        # ----------------------------------------------------
        # Cek apakah row merupakan mata pelajaran
        # ----------------------------------------------------

        subject = None

        # Cari subject terpanjang terlebih dahulu
        # supaya "Bahasa Indonesia Lanjut" tidak terbaca sebagai
        # "Bahasa Indonesia"
        for s in sorted(subjects.values(), key=len, reverse=True):
            if re.search(
                rf"(?<!\w){re.escape(s)}(?!\w)",
                text,
                re.IGNORECASE
            ):
                subject = s
                break

        # Bukan row mata pelajaran
        if subject is None:
            continue


        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print(
            f"\nROW {index}:"
        )

        print(text)


        # ----------------------------------------------------
        # Ambil semua angka
        # ----------------------------------------------------

        # Ambil angka setelah nama mata pelajaran
        #
        # Contoh:
        #
        # 1,393
        # 133,408
        # 60.92
        # 44.62
        # 61.47
        # 77.19
        # 13.00
        # 57.87%
        # 32.82%
        # 7.71%
        # 1.60%
        #
        # Total = 11 angka

        pattern = (
            rf"{re.escape(subject)}\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+)\s+"
            r"([\d,.]+%)\s+"
            r"([\d,.]+%)\s+"
            r"([\d,.]+%)\s+"
            r"([\d,.]+%)"
        )


        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )


        # ----------------------------------------------------
        # Kalau tidak cocok
        # ----------------------------------------------------

        if not match:

            print(
                "Gagal parsing:",
                subject
            )

            continue


        # ----------------------------------------------------
        # Ambil nilai
        # ----------------------------------------------------

        values = list(
            match.groups()
        )


        if len(values) != 11:

            print(
                "Jumlah nilai tidak sesuai:",
                len(values)
            )

            continue


        # ----------------------------------------------------
        # Bersihkan angka
        # ----------------------------------------------------

        values = [
            clean_number(v)
            for v in values
        ]


        # ----------------------------------------------------
        # Ambil nomor
        # ----------------------------------------------------

        no_match = re.match(
            r"^\s*(\d+)",
            text
        )


        if no_match:

            no = int(
                no_match.group(1)
            )

        else:

            no = len(hasil) + 1


        # ----------------------------------------------------
        # Buat data
        # ----------------------------------------------------

        data = {

            "provinsi":
            nama_provinsi,

            "no":
            no,

            "mata_pelajaran":
            subject,

            "jumlah_sekolah":
            values[0],

            "jumlah_siswa":
            values[1],

            "rerata":
            values[2],

            "persentil_10":
            values[3],

            "median":
            values[4],

            "persentil_90":
            values[5],

            "standar_deviasi":
            values[6],

            "istimewa":
            values[7],

            "baik":
            values[8],

            "memadai":
            values[9],

            "kurang":
            values[10]

        }


        hasil.append(data)


    return hasil


# ============================================================
# BUKA WEBSITE
# ============================================================

print(
    "Membuka website..."
)

driver.get(URL)


# Tunggu halaman selesai dimuat
wait.until(
    EC.presence_of_all_elements_located(
        (By.TAG_NAME, "select")
    )
)


print(
    "Website berhasil dibuka."
)


# ============================================================
# PILIH WILAYAH = PROVINSI
# ============================================================

selects = driver.find_elements(
    By.TAG_NAME,
    "select"
)

print(
    "Dropdown awal:",
    len(selects)
)


if len(selects) < 3:

    raise Exception(
        "Dropdown wilayah tidak ditemukan."
    )


wilayah = Select(
    selects[2]
)


print(
    "Memilih wilayah: Provinsi"
)


wilayah.select_by_value(
    "provinsi"
)


# ============================================================
# TUNGGU DROPDOWN PROVINSI
# ============================================================

def province_dropdown_ready(driver):

    selects = driver.find_elements(
        By.TAG_NAME,
        "select"
    )

    if len(selects) < 4:
        return False


    try:

        options = Select(
            selects[3]
        ).options


        return len(options) >= 10


    except:

        return False


wait.until(
    province_dropdown_ready
)


# ============================================================
# AMBIL DAFTAR PROVINSI
# ============================================================

selects = driver.find_elements(
    By.TAG_NAME,
    "select"
)


province_select = Select(
    selects[3]
)


provinces = []


for option in province_select.options:

    value = option.get_attribute(
        "value"
    )

    name = option.text.strip()


    if not value:
        continue


    provinces.append(
        {
            "value": value,
            "name": name
        }
    )


print(
    f"\nDitemukan {len(provinces)} provinsi."
)


# ============================================================
# TEMPAT MENYIMPAN SEMUA DATA
# ============================================================

all_data = []


# ============================================================
# LOOP SEMUA PROVINSI
# ============================================================

for province in provinces:

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"PROSES: {province['name']}"
    )

    print(
        "=" * 70
    )


    try:

        # ----------------------------------------------------
        # Ambil dropdown terbaru
        # ----------------------------------------------------

        selects = driver.find_elements(
            By.TAG_NAME,
            "select"
        )


        if len(selects) < 4:

            print(
                "Dropdown provinsi tidak ditemukan."
            )

            continue


        province_select = Select(
            selects[3]
        )


        # ----------------------------------------------------
        # Pilih provinsi
        # ----------------------------------------------------

        print(
            "Memilih:",
            province["name"]
        )


        province_select.select_by_value(
            province["value"]
        )


        # ----------------------------------------------------
        # Pilih 200 data jika tersedia
        # ----------------------------------------------------

        selects = driver.find_elements(
            By.TAG_NAME,
            "select"
        )


        if len(selects) >= 5:

            try:

                jumlah = Select(
                    selects[4]
                )


                jumlah.select_by_value(
                    "200"
                )


            except Exception:

                pass


        # ----------------------------------------------------
        # Tunggu perubahan data
        # ----------------------------------------------------

        print(
            "Menunggu data..."
        )


        province_name = (
            province["name"]
            .split("-", 1)[-1]
            .strip()
            .upper()
        )


        def data_loaded(driver):

            body = driver.find_element(
                By.TAG_NAME,
                "body"
            ).text.upper()


            return (
                province_name in body
                and
                "RERATA NILAI PER MATA PELAJARAN"
                in body
            )


        wait.until(
            data_loaded
        )


        time.sleep(1)


        # ----------------------------------------------------
        # Ambil statistik
        # ----------------------------------------------------

        data = ambil_statistik_mapel(
            province["name"]
        )


        # ----------------------------------------------------
        # Simpan
        # ----------------------------------------------------

        if data:

            all_data.extend(
                data
            )


            print(
                f"\nBerhasil mengambil {len(data)} mata pelajaran."
            )


        else:

            print(
                "\nTidak ada data mata pelajaran."
            )


    except TimeoutException:

        print(
            "\nTIMEOUT:",
            province["name"]
        )


    except Exception as e:

        print(
            "\nERROR:",
            province["name"]
        )

        print(
            repr(e)
        )


# ============================================================
# SIMPAN CSV
# ============================================================

print(
    "\n"
    + "=" * 70
)

print(
    "SELESAI"
)

print(
    "=" * 70
)


if all_data:

    df = pd.DataFrame(
        all_data
    )


    # --------------------------------------------------------
    # Konversi kolom numerik
    # --------------------------------------------------------

    numeric_columns = [

        "no",

        "jumlah_sekolah",

        "jumlah_siswa",

        "rerata",

        "persentil_10",

        "median",

        "persentil_90",

        "standar_deviasi",

        "istimewa",

        "baik",

        "memadai",

        "kurang"

    ]


    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    # --------------------------------------------------------
    # Urutkan
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "provinsi",
            "no"
        ]
    )


    # --------------------------------------------------------
    # Simpan
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )


    print(
        "\nFile berhasil dibuat:"
    )

    print(
        OUTPUT
    )


    print(
        "\nJumlah total data:",
        len(df)
    )


    print(
        "Jumlah provinsi:",
        df["provinsi"].nunique()
    )


    print(
        "Jumlah mata pelajaran:",
        df["mata_pelajaran"].nunique()
    )


    print(
        "\nJumlah data per provinsi:"
    )

    print(
        df.groupby("provinsi")
        .size()
        .to_string()
    )


    print(
        "\nPreview:"
    )

    print(
        df.head(10).to_string(
            index=False
        )
    )


else:

    print(
        "\nTidak ada data yang berhasil diambil."
    )


# ============================================================
# TUTUP BROWSER
# ============================================================

driver.quit()


print(
    "\nBrowser ditutup."
)