# DUNGEON SURVIVAL: Bayesian Shadow Ninja

**Mata Kuliah:** 10S3109 - Kecerdasan Buatan (CERTAN)  
**Topik:** Uncertainty (Ketidakpastian) – Teorema Bayes & Expected Utility (Versi Hunter Assassin × Wumpus World)

---

## Deskripsi Proyek

**"DUNGEON SURVIVAL: Bayesian Shadow Ninja"** adalah game stealth-action 2D top-down berkecepatan tinggi yang menggabungkan gameplay aksi taktis ala *Hunter Assassin* dengan sistem penalaran ketidakpastian (*Uncertainty AI*) bergaya *Wumpus World*.

Peta dungeon diperbanyak menjadi **43 Ruangan Beragam Bentuk (Multi-Shape Rooms)** yang ditampilkan secara langsung dalam **1 layar penuh**. 

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

- **W, A, S, D** atau **Tombol Panah**: Bergerak lincah
- **[SPASI]**: **Serangan Manual Pedang Katana** (Efek tebasan sabit emas-perak & tebasan bilah pedang). Menyerang tidak lagi otomatis; tekan SPASI saat berada di samping/belakang monster. Saat **Skill 2 (Vanish)** aktif, jarak serangan pertama **meningkat drastis** (85px Ambush Strike) untuk menyergap musuh dari kejauhan!
- **Serang dari Samping / Belakang**: 3 hit untuk membunuh saat monster patroli; monster langsung mengamuk & kebal saat mengejar, wajib bersembunyi di balik balok tengah.
- **Hindari Serangan Depan**: Monster akan menangkis dan mencakar balik jika diserang frontal atau saat sedang mengejar.
- **[1] Skill 1 — Dash Strike**: Menerjang ke depan dan melancarkan tebasan beruntun berkecepatan tinggi sepanjang pedang ke monster di depannya hingga langsung mati (Cooldown: **2,3 detik** — terlindung dari menembus dinding)
- **[2] Skill 2 — Vanish**: Menghilang (transparan), monster tidak dapat mendeteksi keberadaan ninja selama **5 detik** atau sampai menyerang (Cooldown: **9 detik**)
- **[H]**: Ganti Tingkat Kesulitan (**NORMAL** / **HARD**)
- **[R]**: Mengulang permainan (*Restart*) setelah menang atau kalah
