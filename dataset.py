import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
#  DATASET.PY - Konfigurasi & Data Game
#  "DUNGEON SURVIVAL: Bayesian Shadow Ninja"
#  Mata Kuliah: 10S3109 - Kecerdasan Buatan (CERTAN)
#  Topik: Uncertainty (Teorema Bayes & Expected Utility)
# ============================================================

import math

# ======================= RESOLUSI LAYAR =======================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
GAME_AREA_WIDTH = 880     # Area permainan (sisi kiri)
PANEL_WIDTH = 320         # Panel AI Bayesian (sisi kanan)
FPS = 60
TILE_SIZE = 40

# ======================= PALET WARNA =========================
# --- Warna Dasar ---
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
DARK_GRAY    = (40, 40, 40)
GRAY         = (100, 100, 100)
LIGHT_GRAY   = (180, 180, 180)
RED          = (220, 30, 30)
GREEN        = (30, 180, 30)
BLUE         = (30, 30, 220)
YELLOW       = (255, 220, 0)
ORANGE       = (255, 140, 0)
PURPLE       = (140, 30, 180)

# --- Warna Lingkungan Dungeon ---
COLOR_FLOOR            = (40, 36, 46)
COLOR_FLOOR_ALT        = (46, 42, 54)
COLOR_FLOOR_TILE_LINE  = (32, 28, 38)
COLOR_WALL             = (65, 60, 75)
COLOR_WALL_BORDER      = (38, 34, 46)
COLOR_WALL_HIGHLIGHT   = (85, 80, 98)
COLOR_WALL_SHADOW      = (28, 25, 34)

# --- Balok / Kotak Pelindung Khas Hunter Assassin (Green Tactical Blocks) ---
COLOR_CONTAINER          = (42, 125, 70)
COLOR_CONTAINER_DARK     = (28, 85, 48)
COLOR_CONTAINER_BORDER   = (20, 65, 36)
COLOR_CONTAINER_HIGHLIGHT= (60, 160, 95)

# --- Pintu, Portal & Efek Dunia ---
COLOR_PORTAL_PAD       = (40, 120, 180)
COLOR_PORTAL_GLOW      = (80, 220, 255)
COLOR_DOOR_FRAME       = (80, 75, 95)
COLOR_DOOR_OPEN        = (30, 160, 50)
COLOR_DOOR_GLOW_SAFE   = (60, 200, 80)
COLOR_DOOR_GLOW_DANGER = (200, 60, 60)
COLOR_FOG              = (12, 10, 16)

# --- Warna Karakter Ninja ---
COLOR_NINJA_BODY       = (25, 25, 30)
COLOR_NINJA_INNER      = (35, 35, 40)
COLOR_NINJA_MASK       = (20, 20, 25)
COLOR_NINJA_EYES       = (220, 230, 255)
COLOR_NINJA_PUPIL      = (40, 60, 120)
COLOR_NINJA_HEADBAND   = (200, 30, 30)
COLOR_NINJA_TASSEL     = (180, 25, 25)
COLOR_NINJA_ARMOR      = (55, 55, 60)
COLOR_NINJA_ARMOR_EDGE = (80, 80, 90)
COLOR_NINJA_KATANA     = (185, 190, 200)
COLOR_NINJA_KATANA_EDGE= (220, 225, 235)
COLOR_NINJA_SCABBARD   = (60, 30, 20)
COLOR_NINJA_BELT       = (50, 30, 20)

# --- Warna Monster per Tier ---
# Tier 1: Goblin Scout (kecil, hijau)
COLOR_GOBLIN           = (60, 140, 50)
COLOR_GOBLIN_DARK      = (40, 100, 35)
COLOR_GOBLIN_EYES      = (255, 255, 0)
COLOR_GOBLIN_SKIN      = (80, 160, 60)
COLOR_GOBLIN_NOSE      = (50, 120, 40)
COLOR_GOBLIN_EAR       = (70, 150, 55)
COLOR_GOBLIN_FANG      = (230, 230, 200)

# Tier 2: Orc Sentry (sedang, oranye/tembaga)
COLOR_ORC              = (180, 120, 50)
COLOR_ORC_DARK         = (130, 85, 35)
COLOR_ORC_EYES         = (255, 80, 0)
COLOR_ORC_SKIN         = (190, 135, 65)
COLOR_ORC_ARMOR        = (100, 80, 40)
COLOR_ORC_ARMOR_EDGE   = (130, 110, 60)
COLOR_ORC_TUSK         = (220, 210, 180)

# Tier 3: Shadow Stalker (besar, ungu gelap)
COLOR_STALKER          = (80, 30, 120)
COLOR_STALKER_DARK     = (50, 15, 80)
COLOR_STALKER_EYES     = (200, 0, 255)
COLOR_STALKER_EYES2    = (160, 0, 220)
COLOR_STALKER_SKIN     = (90, 40, 130)
COLOR_STALKER_HORN     = (60, 25, 90)
COLOR_STALKER_FANG     = (180, 160, 200)
COLOR_STALKER_AURA     = (100, 0, 180)

# Tier 4: Dungeon Warden (raksasa, merah darah/hitam)
COLOR_WARDEN           = (160, 20, 20)
COLOR_WARDEN_DARK      = (100, 10, 10)
COLOR_WARDEN_EYES      = (255, 50, 0)
COLOR_WARDEN_SKIN      = (140, 30, 25)
COLOR_WARDEN_ARMOR     = (40, 40, 45)
COLOR_WARDEN_ARMOR_EDGE= (70, 65, 70)
COLOR_WARDEN_HORN      = (80, 20, 15)
COLOR_WARDEN_FANG      = (200, 180, 160)
COLOR_WARDEN_JAW       = (120, 15, 15)

# --- Warna UI ---
COLOR_HP_BAR     = (220, 40, 40)
COLOR_HP_BG      = (60, 20, 20)
COLOR_HP_BORDER  = (150, 30, 30)
COLOR_GOLD_ICON  = (255, 215, 0)
COLOR_PANEL_BG   = (18, 18, 28)
COLOR_PANEL_BG2  = (25, 25, 38)
COLOR_PANEL_BORDER = (55, 55, 75)
COLOR_PANEL_TEXT = (200, 200, 220)
COLOR_PANEL_TITLE = (240, 220, 160)
COLOR_PANEL_HIGHLIGHT = (100, 180, 255)

# --- Warna Efek Visual ---
COLOR_CLAW_MARK    = (200, 20, 20)
COLOR_DAMAGE_TEXT  = (255, 60, 60)
COLOR_HEAL_TEXT    = (60, 255, 60)
COLOR_KILL_TEXT    = (255, 215, 0)
COLOR_CONFETTI     = [
    (255, 50, 50), (50, 255, 50), (50, 100, 255),
    (255, 255, 50), (255, 50, 255), (50, 255, 255),
    (255, 150, 50), (150, 50, 255), (255, 100, 180),
    (100, 255, 150), (200, 200, 50), (50, 200, 200),
]

# ===================== KONFIGURASI NINJA =====================
NINJA_CONFIG = {
    'hp': 100,
    'max_hp': 100,
    'speed': 5.2,           # Kecepatan berjalan cepat responsif ala Hunter Assassin
    'radius': 11,           # Radius collision
    'attack_range': 28,     # Jarak sentuh untuk assassination
    'kill_angle': 120,      # Sudut blindspot monster (derajat)
    'vision_range': 200,    # Jangkauan senter
    'vision_angle': 75,     # Sudut kerucut senter (derajat)
    'ambient_radius': 60,   # Radius cahaya ambient di sekitar ninja
}

# ==================== STATISTIK MONSTER (LEBIH BUAS) ======================
MONSTER_STATS = {
    'goblin_scout': {
        'name': 'Goblin Scout',
        'name_id': 'Goblin Pengintai',
        'tier': 1,
        'hp': 30,
        'damage': 10,
        'speed': 2.6,
        'radius': 10,
        'detection_range': 150,
        'vision_angle': 65,
        'chase_speed': 4.2,
        'color': COLOR_GOBLIN,
        'color_dark': COLOR_GOBLIN_DARK,
        'eye_color': COLOR_GOBLIN_EYES,
        'gold_reward': 15,
        'sound_freq': 320,
        'sound_type': 'squeak',
        'attack_cooldown': 0.8,
        'description': 'Monster kecil gesit dengan telinga runcing agresif',
    },
    'orc_sentry': {
        'name': 'Orc Sentry',
        'name_id': 'Orc Penjaga',
        'tier': 2,
        'hp': 60,
        'damage': 18,
        'speed': 2.2,
        'radius': 13,
        'detection_range': 170,
        'vision_angle': 60,
        'chase_speed': 3.6,
        'color': COLOR_ORC,
        'color_dark': COLOR_ORC_DARK,
        'eye_color': COLOR_ORC_EYES,
        'gold_reward': 30,
        'sound_freq': 180,
        'sound_type': 'growl',
        'attack_cooldown': 1.0,
        'description': 'Penjaga orc bertaring buas dan berpelindung bahu',
    },
    'shadow_stalker': {
        'name': 'Shadow Stalker',
        'name_id': 'Pemburu Bayang',
        'tier': 3,
        'hp': 90,
        'damage': 25,
        'speed': 2.8,
        'radius': 15,
        'detection_range': 190,
        'vision_angle': 55,
        'chase_speed': 4.6,
        'color': COLOR_STALKER,
        'color_dark': COLOR_STALKER_DARK,
        'eye_color': COLOR_STALKER_EYES,
        'gold_reward': 50,
        'sound_freq': 120,
        'sound_type': 'hiss',
        'attack_cooldown': 0.75,
        'description': 'Pemburu bayang bermata empat sangat cepat dan ganas',
    },
    'dungeon_warden': {
        'name': 'Dungeon Warden',
        'name_id': 'Sipir Dungeon',
        'tier': 4,
        'hp': 140,
        'damage': 35,
        'speed': 2.2,
        'radius': 17,
        'detection_range': 200,
        'vision_angle': 50,
        'chase_speed': 3.5,
        'color': COLOR_WARDEN,
        'color_dark': COLOR_WARDEN_DARK,
        'eye_color': COLOR_WARDEN_EYES,
        'gold_reward': 80,
        'sound_freq': 70,
        'sound_type': 'roar',
        'attack_cooldown': 1.1,
        'description': 'Raksasa buas bertanduk besar dengan serangan telak',
    },
}

# ==================== KONFIGURASI TINGKAT KESULITAN ======================
DIFFICULTY_CONFIG = {
    'NORMAL': {
        'ninja_speed_mult': 1.0,
        'monster_speed_mult': 1.0,
        'monster_chase_mult': 1.0,
        'monster_damage_mult': 1.0,
        'monster_cooldown_mult': 1.0,
        'detection_mult': 1.0,
        'name_id': 'NORMAL',
        'color': (60, 220, 100),
    },
    'HARD': {
        'ninja_speed_mult': 1.15,        # Ninja bergerak lincah (5.2 * 1.15 = 6.0)
        'monster_speed_mult': 1.15,       # Monster patroli lebih cepat
        'monster_chase_mult': 1.25,       # Monster mengejar sangat buas & agresif
        'monster_damage_mult': 1.85,      # DAMAGE JAUH LEBIH SAKIT & MEMATIKAN!
        'monster_cooldown_mult': 0.60,    # Serangan bertubi-tubi tanpa henti
        'detection_mult': 1.20,           # Sensor pandangan lebih tajam
        'name_id': 'HARD (SANGAT SAKIT & BUAS)',
        'color': (255, 60, 60),
    }
}

# ================ JENIS ANCAMAN (UNTUK BAYES) ================
THREAT_TYPES = ['safe', 'goblin_scout', 'orc_sentry', 'shadow_stalker', 'dungeon_warden']

# Label ancaman dalam Bahasa Indonesia
THREAT_NAMES_ID = {
    'safe': 'Aman (Kosong)',
    'goblin_scout': 'Goblin Pengintai',
    'orc_sentry': 'Orc Penjaga',
    'shadow_stalker': 'Pemburu Bayang',
    'dungeon_warden': 'Sipir Dungeon',
}

# ============= PROBABILITAS PRIOR PER STAGE =================
# P(H) = probabilitas awal sebelum melihat evidensi
STAGE_PRIORS = {
    1: {
        'safe':             0.45,
        'goblin_scout':     0.40,
        'orc_sentry':       0.10,
        'shadow_stalker':   0.04,
        'dungeon_warden':   0.01,
    },
    2: {
        'safe':             0.35,
        'goblin_scout':     0.30,
        'orc_sentry':       0.25,
        'shadow_stalker':   0.08,
        'dungeon_warden':   0.02,
    },
    3: {
        'safe':             0.25,
        'goblin_scout':     0.15,
        'orc_sentry':       0.30,
        'shadow_stalker':   0.20,
        'dungeon_warden':   0.10,
    },
    4: {
        'safe':             0.15,
        'goblin_scout':     0.05,
        'orc_sentry':       0.20,
        'shadow_stalker':   0.35,
        'dungeon_warden':   0.25,
    },
    5: {
        'safe':             0.10,
        'goblin_scout':     0.00,
        'orc_sentry':       0.10,
        'shadow_stalker':   0.30,
        'dungeon_warden':   0.50,
    },
}

# Probabilitas Prior untuk Mode HARD (Ruangan jalan aman SANGAT SEDIKIT, hampir semua ruangan dihuni monster buas)
STAGE_PRIORS_HARD = {
    1: {
        'safe':             0.12,   # Ruangan jalan aman sangat langka
        'goblin_scout':     0.40,
        'orc_sentry':       0.30,
        'shadow_stalker':   0.15,
        'dungeon_warden':   0.03,
    },
    2: {
        'safe':             0.08,
        'goblin_scout':     0.25,
        'orc_sentry':       0.35,
        'shadow_stalker':   0.22,
        'dungeon_warden':   0.10,
    },
    3: {
        'safe':             0.05,
        'goblin_scout':     0.15,
        'orc_sentry':       0.30,
        'shadow_stalker':   0.32,
        'dungeon_warden':   0.18,
    },
    4: {
        'safe':             0.03,
        'goblin_scout':     0.05,
        'orc_sentry':       0.20,
        'shadow_stalker':   0.40,
        'dungeon_warden':   0.32,
    },
    5: {
        'safe':             0.01,   # Hampir mustahil menemukan bilik kosong di lantai dalam
        'goblin_scout':     0.00,
        'orc_sentry':       0.09,
        'shadow_stalker':   0.35,
        'dungeon_warden':   0.55,
    },
}

# ============= MATRIKS LIKELIHOOD (KUNCI BAYES) =============
# P(E|H) = probabilitas mendengar petunjuk audio tertentu
#           JIKA jenis ancaman di balik pintu adalah H
AUDIO_CLUES = ['silence', 'faint_sound', 'growl', 'heavy_growl', 'roar']

LIKELIHOOD_MATRIX = {
    #                     silence  faint    growl   heavy    roar
    'safe':             [ 0.78,   0.15,    0.04,   0.02,   0.01 ],
    'goblin_scout':     [ 0.10,   0.45,    0.30,   0.10,   0.05 ],
    'orc_sentry':       [ 0.05,   0.10,    0.40,   0.35,   0.10 ],
    'shadow_stalker':   [ 0.12,   0.05,    0.10,   0.30,   0.43 ],
    'dungeon_warden':   [ 0.02,   0.03,    0.05,   0.25,   0.65 ],
}

# Nama petunjuk audio (Bahasa Indonesia)
CLUE_NAMES = {
    'silence':      'Hening',
    'faint_sound':  'Suara Samar',
    'growl':        'Geraman',
    'heavy_growl':  'Geraman Berat',
    'roar':         'Raungan Keras',
}

# ============= MATRIKS UTILITAS (EXPECTED UTILITY) ===========
# U(masuk, keadaan) = nilai keuntungan/kerugian memasuki ruangan
UTILITY_MATRIX = {
    'safe':             85,     # Sangat menguntungkan
    'goblin_scout':     35,     # Mudah dikalahkan → untung sedang
    'orc_sentry':       -10,    # Cukup berbahaya
    'shadow_stalker':   -45,    # Sangat berbahaya
    'dungeon_warden':   -75,    # Mematikan
}

# ============ LAYOUT DINDING INTERNAL RUANGAN ================
# Format: list of (x_offset, y_offset, width, height) relatif
# terhadap area dalam ruangan (di dalam batas dinding luar)
ROOM_LAYOUTS = {
    'layout_open': [],
    'layout_pillar_4': [
        (150, 110, 35, 35),
        (420, 110, 35, 35),
        (150, 300, 35, 35),
        (420, 300, 35, 35),
    ],
    'layout_corridor_h': [
        (0, 170, 250, 28),
        (360, 250, 250, 28),
    ],
    'layout_maze_v': [
        (110, 0, 28, 190),
        (230, 200, 28, 250),
        (380, 0, 28, 230),
        (510, 180, 28, 270),
    ],
    'layout_cross': [
        (220, 130, 180, 24),
        (300, 50, 24, 180),
        (220, 300, 180, 24),
        (300, 240, 24, 180),
    ],
    'layout_zigzag': [
        (90, 0, 24, 210),
        (230, 230, 24, 220),
        (380, 0, 24, 210),
        (520, 230, 24, 220),
    ],
    'layout_L': [
        (150, 0, 28, 250),
        (150, 222, 250, 28),
    ],
    'layout_T': [
        (120, 200, 380, 28),
        (290, 0, 28, 200),
    ],
}

LAYOUT_NAMES = list(ROOM_LAYOUTS.keys())

# ============ KONFIGURASI RUANGAN PER STAGE ==================
# 5 Stage × 3 Pintu = 15 Ruangan
ROOM_INNER_W = 620   # Lebar area dalam ruangan
ROOM_INNER_H = 450   # Tinggi area dalam ruangan
WALL_THICKNESS = 24   # Ketebalan dinding luar
DOOR_WIDTH = 60       # Lebar pintu masuk/keluar

STAGE_ROOMS = {
    1: {
        'A': {'layout': 'layout_open',      'monster_pool': [None, 'goblin_scout']},
        'B': {'layout': 'layout_pillar_4',  'monster_pool': ['goblin_scout', None]},
        'C': {'layout': 'layout_corridor_h','monster_pool': [None, 'goblin_scout', 'goblin_scout']},
    },
    2: {
        'A': {'layout': 'layout_cross',     'monster_pool': ['goblin_scout', 'orc_sentry', None]},
        'B': {'layout': 'layout_maze_v',    'monster_pool': [None, 'goblin_scout', 'orc_sentry']},
        'C': {'layout': 'layout_zigzag',    'monster_pool': ['orc_sentry', 'goblin_scout', None]},
    },
    3: {
        'A': {'layout': 'layout_T',         'monster_pool': ['orc_sentry', 'shadow_stalker', None]},
        'B': {'layout': 'layout_pillar_4',  'monster_pool': ['orc_sentry', None, 'shadow_stalker']},
        'C': {'layout': 'layout_cross',     'monster_pool': ['shadow_stalker', 'orc_sentry', 'orc_sentry']},
    },
    4: {
        'A': {'layout': 'layout_zigzag',    'monster_pool': ['shadow_stalker', 'dungeon_warden', 'orc_sentry']},
        'B': {'layout': 'layout_L',         'monster_pool': ['shadow_stalker', 'shadow_stalker', 'dungeon_warden']},
        'C': {'layout': 'layout_maze_v',    'monster_pool': ['dungeon_warden', 'shadow_stalker', 'orc_sentry']},
    },
    5: {
        'A': {'layout': 'layout_cross',     'monster_pool': ['dungeon_warden', 'shadow_stalker']},
        'B': {'layout': 'layout_zigzag',    'monster_pool': ['dungeon_warden', 'dungeon_warden']},
        'C': {'layout': 'layout_pillar_4',  'monster_pool': ['shadow_stalker', 'dungeon_warden']},
    },
}

# ============ KONFIGURASI AUDIO ===============================
AUDIO_CONFIG = {
    'sample_rate': 44100,
    'channels': 2,           # Stereo
    'bit_depth': -16,        # 16-bit signed
    'buffer_size': 1024,
    'duration_sfx': 0.3,     # Durasi efek suara pendek
    'duration_clue': 1.2,    # Durasi petunjuk audio
    'master_volume': 0.35,
}

# ============ KONFIGURASI UI ==================================
UI_CONFIG = {
    'panel_x': GAME_AREA_WIDTH,
    'panel_width': PANEL_WIDTH,
    'font_size_title': 22,
    'font_size_heading': 18,
    'font_size_normal': 15,
    'font_size_small': 13,
    'font_size_tiny': 11,
    'hp_bar_width': 180,
    'hp_bar_height': 16,
    'padding': 10,
    'line_spacing': 20,
}

# ============ TEKS GAME (BAHASA INDONESIA) ====================
GAME_TEXTS = {
    'title':            'DUNGEON SURVIVAL',
    'subtitle':         'Bayesian Shadow Ninja',
    'start_prompt':     'Tekan ENTER untuk Memulai',
    'stage_prefix':     'LANTAI',
    'door_label':       'PINTU',
    'safe_room':        'Ruangan Aman!',
    'monster_room':     'AWAS! Ada Monster!',
    'room_cleared':     'Ruangan Dibersihkan!',
    'proceed':          'Menuju Pintu Keluar ...',
    'victory':          'KEMENANGAN!',
    'victory_sub':      'Ninja Berhasil Menaklukkan Dungeon!',
    'victory_stats':    'Statistik Akhir',
    'game_over':        'MISI GAGAL',
    'game_over_sub':    'Tekan R untuk Mengulang',
    'bayes_title':      '[ Analisis Bayesian ]',
    'posterior_label':   'Probabilitas Posterior P(H|E)',
    'prior_label':      'Probabilitas Prior P(H)',
    'likelihood_label': 'Likelihood P(E|H)',
    'utility_label':    'Expected Utility',
    'recommendation':   'Rekomendasi Pintu',
    'entropy_label':    'Entropi Shannon H(X)',
    'hp_label':         'HP',
    'gold_label':       'Gold',
    'stage_label':      'Lantai',
    'kills_label':      'Kill',
    'clue_label':       'Petunjuk Audio',
    'controls_hub':     'WASD: Jalan ke Pintu | Dengarkan Petunjuk',
    'controls_room':    'WASD: Gerak | Tabrak Belakang: Bunuh Senyap',
    'analyzing':        'Menganalisis...',
    'safe_indicator':   '[AMAN]',
    'danger_indicator': '[BAHAYA]',
}

# ============ KONFIGURASI KAMERA & EFEK ======================
CAMERA_CONFIG = {
    'victory_zoom_speed': 0.015,  # Kecepatan zoom kemenangan
    'victory_zoom_max': 2.5,      # Zoom maksimum
    'confetti_count': 120,        # Jumlah confetti
    'confetti_speed_min': 1.0,
    'confetti_speed_max': 4.0,
    'damage_text_duration': 45,   # Frame durasi teks damage
    'damage_text_speed': 1.2,     # Kecepatan naik teks damage
    'claw_mark_duration': 30,     # Frame durasi efek cakaran
}