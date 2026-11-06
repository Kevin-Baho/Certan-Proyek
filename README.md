# DUNGEON SURVIVAL: Bayesian Shadow Ninja

**Mata Kuliah:** 10S3109 - Kecerdasan Buatan (CERTAN)  
**Topik:** Uncertainty (Ketidakpastian) – Teorema Bayes & Expected Utility (Versi Hunter Assassin × Wumpus World)

---

## Deskripsi Proyek

**"DUNGEON SURVIVAL: Bayesian Shadow Ninja"** adalah game stealth-action 2D top-down berkecepatan tinggi yang menggabungkan gameplay aksi taktis ala *Hunter Assassin* dengan sistem penalaran ketidakpastian (*Uncertainty AI*) bergaya *Wumpus World*.

Peta dungeon diperbanyak menjadi **43 Ruangan Beragam Bentuk (Multi-Shape Rooms)** yang ditampilkan secara langsung dalam **1 layar penuh**.

---

## Panduan Instalasi & Cara Menjalankan

### 1. Prasyarat Sistem
- **Python**: Versi `3.8` atau yang lebih baru (disarankan Python `3.10` / `3.11` / `3.12`).
- **Sistem Operasi**: Windows, macOS, atau Linux.

### 2. Instalasi Dependensi
Game ini hanya memerlukan pustaka eksternal **Pygame** untuk grafis, audio synthesizer, dan penanganan input. Buka terminal (Command Prompt, PowerShell, atau Terminal) di folder proyek ini, lalu jalankan:

```bash
pip install pygame
```

*(Opsional: Jika memiliki beberapa versi Python di komputer, gunakan `python -m pip install pygame` atau `py -m pip install pygame`)*.

### 3. Menjalankan Permainan
Setelah dependensi terpasang, jalankan berkas utama:

```bash
python dungeon_game.py
```

Jika di Windows menggunakan Python Launcher:
```powershell
py dungeon_game.py
```

---

## Struktur Berkas Proyek

| Berkas | Peran & Deskripsi |
|---|---|
| `dungeon_game.py` | Berkas eksekusi utama (*Main Game Engine*). Mengatur grafis Pygame, pergerakan karakter, logika dash menyergap, monster AI, partikel, audio sintetis, serta antarmuka (HUD & Ikon Skill). |
| `ai_model.py` | Engine inferensi probabilistik: menghitung probabilitas posterior Bayesian $P(H \mid E)$, *Maximum Expected Utility* (MEU), dan Entropi Shannon untuk rekomendasi rute teraman. |
| `dataset.py` | Matriks probabilitas prior kedalaman lantai (`STAGE_PRIORS`, `STAGE_PRIORS_HARD`), tabel likelihood bukti suara (*clue likelihood*), dan matriks utilitas reward/penalty aksi. |
| `README.md` | Dokumentasi lengkap proyek, teori Bayesian, kontrol, dan panduan instalasi. |

---

## Fitur Utama & Pembaruan Game

| Fitur | Deskripsi |
|-------|-----------|
| **43 Ruangan Multi-Shape** | Labirin luas berisikan 43 ruangan dengan beragam bentuk: **Bentuk L (3 subcells)**, **Aula Besar (2×2 subcells)**, **Persegi Panjang Horisontal/Vertikal (2 subcells)**, dan **Bilik Tunggal (1 subcell)**. |
| **Banyak Box Proporsional** | Banyaknya balok hijau persembunyian (*tactical containers*) **menyesuaikan dengan panjang dan luas ruangan** (1 box pada bilik kecil hingga 4 box pada aula besar). |
| **Finish Nampak Sejak Awal** | Ruangan finish/portal ekstraksi **selalu nampak jelas dari awal hingga akhir game** (tidak tertutup kabut hitam), bersinar dengan pilar cyan-emas dan penanda suar `★ FINISH PORTAL ★`. Ruangan finish dijamin 100% bebas monster. |
| **Jalur Kosong Terjamin** | Selalu tersedia setidaknya **1 jalur ruangan kosong (safe path)** menuju ruangan finish tanpa monster, dapat dilalui dengan mengikuti panduan rekomendasi Bayesian MEU. |
| **Tingkat Kesulitan HARD (Buas)** | Pemain dapat menekan tombol **`[H]`** kapan saja untuk beralih antara mode **NORMAL** dan **HARD**. Pada mode HARD, monster bergerak sangat buas & agresif (*chase speed* tinggi, damage +40%, cooldown serang singkat), dan ninja diberikan kecepatan ekstra secepat kilat. |
| **Sistem Kunci Ruangan** | Saat ninja melangkah ke dalam ruangan yang dihuni monster hidup, pintu ruangan **terkunci rapat**. Ninja tidak dapat keluar sampai monster berhasil dieliminasi. |
| **Minesweeper Badge di Kepala** | Angka lencana di atas kepala ninja menunjukkan jumlah monster hidup yang berada di ruangan-ruangan sekitar (🟢0 = Aman, 🟡1 = Waspada, 🟠2 = Bahaya, 🔴3+ = Sangat Berbahaya). |
| **Aturan Tempur Arah (Combat)** | **DILARANG menyerang dari depan** (monster akan langsung mencakar balik). Ninja **HANYA BISA menyerang dari samping atau dari belakang**. |
| **Sistem 3 Hit to Kill** | Setiap monster membutuhkan **3 kali tebasan** dari samping/belakang untuk ditumbangkan (dilengkapi indikator titik HP di atas monster). |
| **Bayangan Halus Tiap Monster** | Setiap monster memiliki bayangan halus di bawah tubuhnya yang bergerak dinamis. |
| **Balok Penutup (Line of Sight)** | Ninja dapat bersembunyi di balik balok hijau untuk memutus garis pandang (*Line of Sight*) monster. |
| **Panel AI Bayesian & MEU** | Panel kanan ($320\text{ px}$) menghitung probabilitas posterior $P(H \mid E)$, *Expected Utility* ($EU$), dan rekomendasi rute teraman (*Maximum Expected Utility* / MEU). |

---

## Dasar Teori Kecerdasan Buatan (Uncertainty)

### 1. Teorema Bayes
Teorema Bayes menghitung probabilitas posterior bahwa ruangan tetangga berisi ancaman tertentu $H_i$, dengan evidensi petunjuk audio $E$:

$$
P(H_i \mid E) = \frac{P(E \mid H_i) \cdot P(H_i)}{\sum_{j} P(E \mid H_j) \cdot P(H_j)}
$$

- $H_i \in \{\text{Aman}, \text{Goblin Scout}, \text{Orc Sentry}, \text{Shadow Stalker}, \text{Dungeon Warden}\}$
- $E \in \{\text{Hening}, \text{Suara Samar}, \text{Geraman}, \text{Geraman Berat}, \text{Raungan}\}$
- $P(H_i)$ : Prior probabilistik per tingkat kedalaman lantai (didukung `STAGE_PRIORS` dan `STAGE_PRIORS_HARD`).
- $P(E \mid H_i)$ : Matriks Likelihood petunjuk audio.

### 2. Maximum Expected Utility (MEU)
$$
EU(a) = \sum_{i} P(H_i \mid E) \cdot U(a, H_i)
$$

$$
a^* = \arg\max_a EU(a)
$$

- $U(\text{Aman}) = +85$
- $U(\text{Goblin}) = +35$
- $U(\text{Orc}) = -10$
- $U(\text{Stalker}) = -45$
- $U(\text{Warden}) = -75$

### 3. Entropi Shannon
$$
H(X) = -\sum_{i} P(x_i) \log_2 P(x_i)
$$

---

## Hirarki Monster

| Tier | Monster | HP | Damage | Sifat & Perilaku |
|:---:|:---|:---:|:---:|:---|
| **1** | **Goblin Scout** | 30 | 10 | Kecil, hijau, telinga runcing, lincah berpatroli |
| **2** | **Orc Sentry** | 60 | 18 | Sedang, tembaga, berpelindung bahu, taring tajam |
| **3** | **Shadow Stalker** | 90 | 25 | Ungu gelap mistis, bertanduk, 4 mata, lari sangat cepat |
| **4** | **Dungeon Warden** | 140 | 35 | Raksasa bertanduk masif, serangan telak mematikan |

---

## Kontrol Permainan & Skill Ninja

- **W, A, S, D** atau **Tombol Panah**: Bergerak lincah di dalam dungeon.
- **[SPASI] — Serangan Dash Menyergap Manual**: 
  - Ninja melakukan dash kilat menyergap ke arah monster dan melancarkan tebasan sabit emas-perak.
  - **Syarat Posisi**: Serangan **hanya bisa dilakukan jika musuh berada di samping atau belakang kita**. Menekan `SPASI` di ruang kosong atau tepat di depan muka musuh tidak akan memicu serangan.
  - Saat **Skill 2 (Vanish)** aktif, jangkauan sergapan meningkat drastis hingga **85 px** untuk menyergap dari bayangan.
  - Tampilan visual bersih tanpa teks angka/kata melayang (*no floating damage text*).
- **[1] Skill 1 — Dash Strike**: Menerjang lurus ke depan dan melancarkan tebasan beruntun berkecepatan tinggi sepanjang pedang ke monster di depannya hingga langsung mati (Cooldown: **2,3 detik** — dilengkapi proteksi anti-tembus dinding dan balok).
- **[2] Skill 2 — Vanish**: Menghilang (transparan), monster tidak dapat mendeteksi keberadaan ninja selama **5 detik** atau sampai melancarkan serangan (Cooldown: **9 detik**).
- **HUD Ikon Skill (Pojok Kiri Bawah)**: Tampilan visual ikon katana dan siluet bayangan dengan overlay cooldown serta timer sisa detik secara real-time.
- **[H]**: Beralih Tingkat Kesulitan (**NORMAL** / **HARD**).
- **[R]**: Mengulang permainan (*Restart*) setelah menang atau kalah.





# Dataset DUNGEON SURVIVAL: Bayesian Shadow Ninja

## 1. Deskripsi Dataset

Dataset **DUNGEON SURVIVAL: Bayesian Shadow Ninja** merupakan kumpulan data yang digunakan dalam proyek game untuk menerapkan metode **Teorema Bayes** dan **Expected Utility**.

Dataset ini berisi informasi mengenai probabilitas kemunculan ancaman, karakteristik monster, petunjuk suara, serta nilai keuntungan dan kerugian dari setiap kondisi.

Dataset digunakan oleh sistem untuk memperkirakan ancaman berdasarkan suara yang didengar pemain dan membantu menentukan keputusan dalam permainan.

## 2. Tujuan Dataset

Dataset ini memiliki beberapa tujuan, yaitu:

- Memperkirakan jenis ancaman berdasarkan petunjuk suara.
- Menghitung probabilitas kemunculan monster menggunakan Teorema Bayes.
- Membantu menentukan keputusan menggunakan Expected Utility.
- Menyediakan informasi karakteristik monster.
- Mendukung pengaturan tingkat kesulitan permainan.

## 3. Struktur Dataset

Dataset tersedia dalam format CSV dengan nama file:

`dataset_dungeon_survival.csv`

Dataset terdiri dari **50 baris data dan 17 kolom**.

### Penjelasan Kolom

| Nama Kolom | Deskripsi |
|---|---|
| `stage` | Tahapan permainan, dari 1 sampai 5. |
| `difficulty` | Tingkat kesulitan permainan, yaitu normal atau hard. |
| `threat` | Kode jenis ancaman. |
| `threat_name_id` | Nama atau identitas ancaman. |
| `prior_probability` | Probabilitas awal kemunculan ancaman. |
| `utility` | Nilai keuntungan atau kerugian dari suatu kondisi. |
| `hp` | Jumlah health point monster. |
| `damage` | Besarnya kerusakan yang diberikan monster. |
| `speed` | Kecepatan monster. |
| `detection_range` | Jarak deteksi monster. |
| `chase_speed` | Kecepatan monster saat mengejar pemain. |
| `gold_reward` | Hadiah gold dari monster. |
| `likelihood_silence` | Kemungkinan munculnya suara diam. |
| `likelihood_faint_sound` | Kemungkinan munculnya suara samar. |
| `likelihood_growl` | Kemungkinan munculnya suara geraman. |
| `likelihood_heavy_growl` | Kemungkinan munculnya geraman keras. |
| `likelihood_roar` | Kemungkinan munculnya suara raungan. |

## 4. Kategori Ancaman

Dataset memiliki lima kategori kondisi ancaman:

| Kategori | Deskripsi |
|---|---|
| Safe | Kondisi aman tanpa ancaman monster. |
| Goblin Scout | Monster jenis goblin. |
| Orc Sentry | Monster jenis orc. |
| Shadow Stalker | Monster penguntit bayangan. |
| Dungeon Warden | Monster penjaga dungeon. |

## 5. Penerapan Teorema Bayes

Teorema Bayes digunakan untuk memperkirakan kemungkinan jenis ancaman berdasarkan petunjuk suara yang diterima pemain.

Informasi yang digunakan meliputi:

- **Prior Probability:** Probabilitas awal kemunculan suatu ancaman.
- **Likelihood:** Kemungkinan suatu petunjuk suara muncul ketika ancaman tertentu terjadi.

Sebagai contoh, ketika pemain mendengar suara raungan (*roar*), sistem menggunakan nilai `prior_probability` dan `likelihood_roar` untuk memperbarui probabilitas setiap ancaman.

Dengan demikian, sistem dapat memperkirakan jenis monster yang kemungkinan berada di sekitar pemain.

## 6. Penerapan Expected Utility

Expected Utility digunakan sebagai dasar pertimbangan dalam menentukan keputusan berdasarkan nilai keuntungan dan kerugian.

Kolom `utility` menyediakan nilai utilitas untuk setiap kondisi ancaman. Nilai tersebut dapat digunakan sistem untuk mempertimbangkan tindakan yang memberikan hasil paling menguntungkan bagi pemain.

## 7. Cara Menggunakan Dataset

Dataset dapat dibaca menggunakan Python dengan bantuan library Pandas.

```python
import pandas as pd

# Membaca dataset
df = pd.read_csv("dataset_dungeon_survival.csv")

# Menampilkan seluruh dataset
print(df)

# Menampilkan lima data pertama
print(df.head())

# Melihat informasi dataset
print(df.info())
```

Pastikan file `dataset_dungeon_survival.csv` berada di direktori yang sesuai dengan lokasi program Python.

## 8. Format dan Sumber Data

- **Format:** CSV (Comma-Separated Values)
- **Jumlah Data:** 50 baris
- **Jumlah Kolom:** 17 kolom
- **Sumber:** Konfigurasi dataset pada proyek DUNGEON SURVIVAL: Bayesian Shadow Ninja.

**Catatan:** Dataset ini merupakan data konfigurasi dan probabilitas yang didefinisikan dalam kode proyek, bukan kumpulan hasil observasi langsung dari aktivitas pemain.

## 9. Kesimpulan

Dataset DUNGEON SURVIVAL: Bayesian Shadow Ninja merupakan komponen pendukung dalam penerapan kecerdasan buatan pada permainan.

Melalui Teorema Bayes, sistem dapat memperkirakan ancaman berdasarkan petunjuk suara. Sementara itu, Expected Utility digunakan untuk membantu mempertimbangkan keputusan berdasarkan nilai keuntungan dan kerugian.

Kombinasi kedua metode tersebut mendukung pengambilan keputusan yang lebih terarah dalam permainan.