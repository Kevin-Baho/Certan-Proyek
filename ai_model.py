import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
#  AI_MODEL.PY - Modul Kecerdasan Buatan & Probabilitas
#  "DUNGEON SURVIVAL: Bayesian Shadow Ninja"
#  Mata Kuliah: 10S3109 - Kecerdasan Buatan (CERTAN)
#  Topik: Uncertainty (Teorema Bayes & Expected Utility)
# ============================================================

import math
import random
import array

from dataset import (
    THREAT_TYPES, STAGE_PRIORS, STAGE_PRIORS_HARD, LIKELIHOOD_MATRIX, AUDIO_CLUES,
    UTILITY_MATRIX, MONSTER_STATS, AUDIO_CONFIG, NINJA_CONFIG,
    CLUE_NAMES, THREAT_NAMES_ID,
)


# ============================================================
#  KELAS: BayesianThreatAnalyzer
#  Implementasi Teorema Bayes untuk analisis ancaman dungeon.
#
#  Rumus Bayes:
#      P(H_i | E) = P(E | H_i) * P(H_i)  /  Sigma_j P(E | H_j) * P(H_j)
#
#  - H_i  = hipotesis ke-i (jenis ancaman: aman / goblin / orc / stalker / warden)
#  - E    = evidensi (petunjuk audio yang terdengar dari balik pintu)
#  - P(H) = probabilitas prior (dari STAGE_PRIORS, berubah tiap lantai)
#  - P(E|H) = likelihood (dari LIKELIHOOD_MATRIX)
# ============================================================
class BayesianThreatAnalyzer:
    """Kalkulator probabilitas posterior menggunakan Teorema Bayes."""

    def __init__(self):
        self.threat_types = THREAT_TYPES
        self.likelihood = LIKELIHOOD_MATRIX
        self.clue_index = {clue: i for i, clue in enumerate(AUDIO_CLUES)}

    # ---------- Ambil distribusi prior ----------
    def get_prior(self, stage_depth, is_hard=False):
        """
        Ambil distribusi prior P(H) berdasarkan kedalaman lantai dan mode kesulitan.
        Lantai lebih dalam -> monster lebih kuat lebih mungkin muncul.
        Mode HARD -> probabilitas monster buas lebih tinggi.
        """
        priors_source = STAGE_PRIORS_HARD if is_hard else STAGE_PRIORS
        priors = priors_source.get(stage_depth, priors_source[5])
        return {t: priors[t] for t in self.threat_types}

    # ---------- Likelihood satu clue ----------
    def compute_likelihood(self, threat_type, clue):
        """Hitung P(clue | threat_type) dari matriks likelihood."""
        idx = self.clue_index.get(clue, 0)
        return self.likelihood[threat_type][idx]

    # ---------- Posterior satu clue ----------
    def compute_posterior(self, stage_depth, observed_clue, is_hard=False):
        """
        Hitung distribusi posterior P(H|E) untuk satu petunjuk audio.

        Parameter:
            stage_depth  : int   - kedalaman lantai (1-5)
            observed_clue: str   - petunjuk audio dari AUDIO_CLUES
            is_hard      : bool  - mode kesulitan HARD

        Return:
            dict {threat_type: float} - distribusi posterior
        """
        priors = self.get_prior(stage_depth, is_hard=is_hard)

        # Hitung joint: P(E|H) * P(H)
        joint = {}
        for threat in self.threat_types:
            lk = self.compute_likelihood(threat, observed_clue)
            joint[threat] = lk * priors[threat]

        # Marginal: P(E) = Sigma P(E|H) * P(H)
        marginal = sum(joint.values())

        # Posterior: P(H|E) = joint / marginal
        if marginal > 0:
            return {t: joint[t] / marginal for t in self.threat_types}
        else:
            uniform = 1.0 / len(self.threat_types)
            return {t: uniform for t in self.threat_types}

    # ---------- Posterior multi-clue (update iteratif) ----------
    def compute_posterior_multi(self, stage_depth, clues_list):
        """
        Hitung posterior dengan beberapa petunjuk berurutan.
        Setiap clue meng-update posterior sebelumnya sebagai prior baru.

        Parameter:
            stage_depth: int
            clues_list : list[str] - urutan petunjuk audio

        Return:
            dict {threat_type: float}
        """
        current = self.get_prior(stage_depth)

        for clue in clues_list:
            joint = {}
            for threat in self.threat_types:
                lk = self.compute_likelihood(threat, clue)
                joint[threat] = lk * current[threat]

            marginal = sum(joint.values())
            if marginal > 0:
                current = {t: joint[t] / marginal for t in self.threat_types}

        return current

    # ---------- Posterior untuk tiga pintu sekaligus ----------
    def analyze_three_doors(self, stage_depth, door_clues):
        """
        Hitung posterior untuk setiap pintu di hub.

        Parameter:
            stage_depth: int
            door_clues : dict {door_label: str_clue}  (misal {'A':'growl','B':'silence','C':'roar'})

        Return:
            dict {door_label: {threat_type: float}}
        """
        result = {}
        for door, clue in door_clues.items():
            result[door] = self.compute_posterior(stage_depth, clue)
        return result


# ============================================================
#  KELAS: ExpectedUtilityAdvisor
#  Implementasi Expected Utility untuk rekomendasi keputusan.
#
#  Rumus:
#      EU(a) = Sigma_i  P(H_i | E) * U(a, H_i)
#
#  - a    = aksi (memasuki pintu tertentu)
#  - H_i  = keadaan di balik pintu
#  - U(a,H) = utilitas dari UTILITY_MATRIX
#  Keputusan optimal: argmax_a EU(a)  (Maximum Expected Utility / MEU)
# ============================================================
class ExpectedUtilityAdvisor:
    """Penasehat keputusan berdasarkan Maximum Expected Utility (MEU)."""

    def __init__(self):
        self.utility_matrix = UTILITY_MATRIX

    def compute_expected_utility(self, posterior):
        """
        Hitung EU untuk satu aksi (masuk satu pintu).

        Parameter:
            posterior: dict {threat_type: float}

        Return:
            float - nilai expected utility
        """
        eu = 0.0
        for threat, prob in posterior.items():
            u = self.utility_matrix.get(threat, 0)
            eu += prob * u
        return eu

    def recommend_door(self, door_posteriors):
        """
        Rekomendasikan pintu terbaik berdasarkan MEU.

        Parameter:
            door_posteriors: dict {door_label: posterior_dict}

        Return:
            (best_door, eu_scores)
            - best_door : str
            - eu_scores : dict {door_label: float}
        """
        eu_scores = {}
        for door, posterior in door_posteriors.items():
            eu_scores[door] = self.compute_expected_utility(posterior)

        best_door = max(eu_scores, key=eu_scores.get)
        return best_door, eu_scores

    def get_risk_level(self, eu_score):
        """
        Kategorikan level risiko dari skor EU.

        Return:
            (label_str, color_rgb)
        """
        if eu_score >= 50:
            return 'AMAN',    (30, 200, 50)
        elif eu_score >= 15:
            return 'RENDAH',  (120, 200, 50)
        elif eu_score >= -15:
            return 'SEDANG',  (220, 200, 40)
        elif eu_score >= -50:
            return 'TINGGI',  (220, 120, 30)
        else:
            return 'BAHAYA',  (220, 40, 40)

    def format_eu_breakdown(self, posterior):
        """
        Buat rincian perhitungan EU untuk ditampilkan di panel.

        Return:
            list of (threat_name, prob, utility, contrib)
        """
        breakdown = []
        for threat in THREAT_TYPES:
            prob = posterior.get(threat, 0)
            util = self.utility_matrix.get(threat, 0)
            contrib = prob * util
            name = THREAT_NAMES_ID.get(threat, threat)
            breakdown.append((name, prob, util, contrib))
        return breakdown


# ============================================================
#  KELAS: ShannonEntropyCalculator
#  Mengukur ketidakpastian dari distribusi probabilitas.
#
#  Rumus Entropi Shannon:
#      H(X) = - Sigma_i  P(x_i) * log2( P(x_i) )
#
#  H tinggi → ketidakpastian tinggi (distribusi merata)
#  H rendah → lebih pasti (satu hipotesis dominan)
# ============================================================
class ShannonEntropyCalculator:
    """Kalkulator Entropi Shannon untuk mengukur ketidakpastian."""

    @staticmethod
    def compute_entropy(distribution):
        """
        Hitung entropi Shannon H(X) dalam satuan bit.

        Parameter:
            distribution: dict {label: probability}

        Return:
            float - entropi (bit)
        """
        h = 0.0
        for p in distribution.values():
            if p > 0:
                h -= p * math.log2(p)
        return h

    @staticmethod
    def max_entropy(n_classes):
        """Entropi maksimum untuk n kelas (distribusi uniform)."""
        if n_classes <= 1:
            return 0.0
        return math.log2(n_classes)

    @staticmethod
    def normalized_entropy(distribution):
        """
        Entropi ternormalisasi [0, 1].
        0 = pasti / tidak ada ketidakpastian
        1 = ketidakpastian maksimum (distribusi uniform)
        """
        n = len(distribution)
        if n <= 1:
            return 0.0
        h = ShannonEntropyCalculator.compute_entropy(distribution)
        h_max = math.log2(n)
        return h / h_max if h_max > 0 else 0.0

    @staticmethod
    def information_gain(prior, posterior):
        """
        Hitung Information Gain = H(prior) - H(posterior).
        Menunjukkan seberapa banyak informasi diperoleh dari evidensi.
        """
        return (ShannonEntropyCalculator.compute_entropy(prior) -
                ShannonEntropyCalculator.compute_entropy(posterior))


# ============================================================
#  KELAS: SoundSynthesizer
#  Sintesis suara prosedural (tanpa file audio eksternal).
#  Menggunakan gelombang PCM 16-bit stereo.
# ============================================================
class SoundSynthesizer:
    """Generator efek suara prosedural menggunakan gelombang PCM."""

    def __init__(self):
        self.sample_rate = AUDIO_CONFIG['sample_rate']

    # ---------- Generator gelombang dasar ----------
    def _generate_wave(self, frequency, duration, volume=0.3, wave_type='sine'):
        """
        Generate data PCM 16-bit stereo mentah.

        Parameter:
            frequency : float - Hz
            duration  : float - detik
            volume    : float - 0.0-1.0
            wave_type : str   - 'sine' / 'square' / 'sawtooth'

        Return:
            bytes - data PCM mentah
        """
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        max_amp = int(32767 * min(volume, 1.0))
        fade_len = int(0.015 * self.sample_rate)  # 15ms fade

        for i in range(n_samples):
            t = i / self.sample_rate
            phase = 2.0 * math.pi * frequency * t

            if wave_type == 'sine':
                val = math.sin(phase)
            elif wave_type == 'square':
                val = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wave_type == 'sawtooth':
                val = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
            else:
                val = math.sin(phase)

            # Envelope fade-in / fade-out
            env = 1.0
            if i < fade_len:
                env = i / max(fade_len, 1)
            elif i > n_samples - fade_len:
                env = (n_samples - i) / max(fade_len, 1)

            sample = int(val * max_amp * env)
            sample = max(-32768, min(32767, sample))
            buf.append(sample)   # Kiri
            buf.append(sample)   # Kanan

        return buf.tobytes()

    # ---------- Suara monster (proximity audio) ----------
    def generate_monster_sound(self, monster_type, volume=0.3):
        """Generate suara khas untuk jenis monster tertentu."""
        if monster_type is None or monster_type == 'safe':
            return self._generate_wave(35, 0.5, volume * 0.08, 'sine')

        stats = MONSTER_STATS.get(monster_type)
        if not stats:
            return self._generate_wave(100, 0.4, volume * 0.15, 'sine')

        freq = stats['sound_freq']
        stype = stats['sound_type']

        if stype == 'squeak':
            return self._generate_wave(freq, 0.35, volume * 0.7, 'sine')
        elif stype == 'growl':
            return self._generate_wave(freq, 0.5, volume * 0.8, 'sawtooth')
        elif stype == 'hiss':
            return self._generate_wave(freq, 0.45, volume * 0.75, 'square')
        elif stype == 'roar':
            return self._generate_wave(freq, 0.7, volume * 0.9, 'sawtooth')
        return self._generate_wave(freq, 0.4, volume * 0.5, 'sine')

    # ---------- Suara petunjuk audio (untuk hub) ----------
    def generate_clue_sound(self, clue_type, volume=0.3):
        """Generate suara petunjuk audio yang terdengar dari balik pintu."""
        mapping = {
            'silence':      (30,  'sine',     0.05),
            'faint_sound':  (200, 'sine',     0.18),
            'growl':        (150, 'sawtooth', 0.28),
            'heavy_growl':  (100, 'sawtooth', 0.38),
            'roar':         (65,  'square',   0.48),
        }
        freq, wave, vmult = mapping.get(clue_type, (100, 'sine', 0.2))
        return self._generate_wave(freq, 1.0, volume * vmult, wave)

    # ---------- Efek suara tebasan katana ----------
    def generate_slash_sound(self, volume=0.35):
        """Suara swoosh tebasan katana saat assassination."""
        n_samples = int(self.sample_rate * 0.18)
        buf = array.array('h')
        mx = int(32767 * volume)

        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 2200 - (t / 0.18) * 1900
            val = math.sin(2.0 * math.pi * freq * t)
            env = 1.0 - (i / n_samples)
            s = int(val * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()

    # ---------- Efek suara cakaran monster ----------
    def generate_claw_sound(self, volume=0.28):
        """Suara efek cakaran saat monster menyerang pemain."""
        n_samples = int(self.sample_rate * 0.14)
        buf = array.array('h')
        mx = int(32767 * volume)

        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 1600 - (t / 0.14) * 1300
            val = math.sin(2.0 * math.pi * freq * t)
            noise = random.uniform(-0.25, 0.25)
            env = 1.0 - (i / n_samples) ** 0.5
            s = int((val * 0.7 + noise * 0.3) * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()

    # ---------- Efek suara pintu terbuka ----------
    def generate_door_sound(self, volume=0.25):
        """Suara berderit pintu terbuka."""
        n_samples = int(self.sample_rate * 0.35)
        buf = array.array('h')
        mx = int(32767 * volume)

        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 140 + 60 * math.sin(2.0 * math.pi * 4 * t)
            val = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - t / 0.35)
            s = int(val * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()

    # ---------- Efek suara deteksi bahaya (Alert Tanda Seru) ----------
    def generate_alert_sound(self, volume=0.35):
        """Suara alert deteksi bahaya tanda seru saat monster mau menyerang."""
        n_samples = int(self.sample_rate * 0.22)
        buf = array.array('h')
        mx = int(32767 * volume)

        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 880 if t < 0.09 else 1175
            val = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - (t / 0.22))
            s = int(val * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()

    # ---------- Efek suara kemenangan ----------
    def generate_victory_sound(self, volume=0.4):
        """Suara fanfare kemenangan (arpeggio naik)."""
        n_samples = int(self.sample_rate * 1.2)
        buf = array.array('h')
        mx = int(32767 * volume)
        notes = [262, 330, 392, 524, 660]

        for i in range(n_samples):
            t = i / self.sample_rate
            note_idx = min(int(t / 0.24), len(notes) - 1)
            freq = notes[note_idx]
            val = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - max(0.0, t - 1.0) / 0.2)
            s = int(val * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()

    # ---------- Efek suara game over ----------
    def generate_gameover_sound(self, volume=0.35):
        """Suara nada turun saat game over."""
        n_samples = int(self.sample_rate * 0.8)
        buf = array.array('h')
        mx = int(32767 * volume)

        for i in range(n_samples):
            t = i / self.sample_rate
            freq = 400 - (t / 0.8) * 300
            val = math.sin(2.0 * math.pi * freq * t)
            env = max(0.0, 1.0 - t / 0.8)
            s = int(val * mx * env)
            s = max(-32768, min(32767, s))
            buf.append(s)
            buf.append(s)

        return buf.tobytes()


# ============================================================
#  KELAS: CombatAnalyzer
#  Analisis peluang tempur berdasarkan posisi & sudut.
# ============================================================
class CombatAnalyzer:
    """Menghitung probabilitas assassination berdasarkan posisi relatif."""

    @staticmethod
    def approach_angle(ninja_pos, monster_pos, monster_facing):
        """
        Hitung sudut pendekatan ninja relatif terhadap arah hadap monster.

        Return:
            float - sudut dalam derajat (0=depan, 180=belakang)
        """
        dx = ninja_pos[0] - monster_pos[0]
        dy = ninja_pos[1] - monster_pos[1]
        angle_to_ninja = math.atan2(dy, dx)

        rel = abs(angle_to_ninja - monster_facing)
        if rel > math.pi:
            rel = 2.0 * math.pi - rel

        return math.degrees(rel)

    @staticmethod
    def is_in_blindspot(ninja_pos, monster_pos, monster_facing, kill_angle=120):
        """
        Apakah ninja berada di blindspot (belakang) monster?

        Parameter:
            kill_angle: total sudut blindspot dalam derajat

        Return:
            bool
        """
        angle = CombatAnalyzer.approach_angle(
            ninja_pos, monster_pos, monster_facing
        )
        return angle >= (180 - kill_angle / 2)

    @staticmethod
    def kill_probability(ninja_pos, monster_pos, monster_facing, kill_angle=120):
        """
        Probabilitas keberhasilan assassination.
        Semakin dekat ke 180° (tepat belakang), semakin tinggi.

        Return:
            float (0.0 - 1.0)
        """
        angle = CombatAnalyzer.approach_angle(
            ninja_pos, monster_pos, monster_facing
        )
        half = kill_angle / 2
        behind = 180 - angle

        if behind <= 0:
            return 0.0
        elif behind >= half:
            return 1.0
        else:
            return behind / half

    @staticmethod
    def detection_probability(dist, det_range, in_vision_cone):
        """
        Probabilitas monster mendeteksi ninja.

        Parameter:
            dist          : float - jarak ninja-monster
            det_range     : float - jangkauan deteksi monster
            in_vision_cone: bool  - apakah ninja di kerucut pandangan

        Return:
            float (0.0 - 1.0)
        """
        if dist > det_range:
            return 0.0
        factor = 1.0 - (dist / det_range)
        if in_vision_cone:
            return min(1.0, factor * 1.5)
        else:
            return factor * 0.25


# ============================================================
#  KELAS: AudioClueGenerator
#  Menghasilkan petunjuk audio probabilistik untuk pintu hub.
# ============================================================
class AudioClueGenerator:
    """
    Menghasilkan petunjuk audio berdasarkan isi sebenarnya di balik pintu.
    Clue bersifat probabilistik menggunakan distribusi likelihood
    sehingga TIDAK selalu akurat (elemen ketidakpastian).
    """

    def __init__(self):
        self.clue_index = {c: i for i, c in enumerate(AUDIO_CLUES)}

    def generate_clue(self, actual_content):
        """
        Generate satu petunjuk audio dari distribusi P(clue | content).

        Parameter:
            actual_content: str atau None - jenis ancaman sebenarnya

        Return:
            str - salah satu dari AUDIO_CLUES
        """
        if actual_content is None:
            actual_content = 'safe'

        probs = LIKELIHOOD_MATRIX.get(actual_content, LIKELIHOOD_MATRIX['safe'])

        r = random.random()
        cumul = 0.0
        for i, clue in enumerate(AUDIO_CLUES):
            cumul += probs[i]
            if r <= cumul:
                return clue

        return AUDIO_CLUES[-1]

    def generate_for_doors(self, door_contents):
        """
        Generate petunjuk audio untuk semua pintu di hub.

        Parameter:
            door_contents: dict {door_label: str_or_None}

        Return:
            dict {door_label: str_clue}
        """
        return {d: self.generate_clue(c) for d, c in door_contents.items()}


# ============================================================
#  FUNGSI UTILITAS GEOMETRI
# ============================================================

def distance(p1, p2):
    """Jarak Euclidean antara dua titik (x,y)."""
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx * dx + dy * dy)


def angle_between(p1, p2):
    """Sudut dari p1 ke p2 dalam radian."""
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def normalize_angle(a):
    """Normalisasi sudut ke [-pi, pi]."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def clamp(val, lo, hi):
    """Batasi nilai dalam [lo, hi]."""
    return max(lo, min(hi, val))


def point_in_rect(px, py, rx, ry, rw, rh):
    """Apakah titik (px,py) di dalam persegi panjang?"""
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def circle_rect_collision(cx, cy, cr, rx, ry, rw, rh):
    """
    Cek tabrakan lingkaran (cx,cy,cr) dengan persegi panjang (rx,ry,rw,rh).
    Return: bool
    """
    nearest_x = clamp(cx, rx, rx + rw)
    nearest_y = clamp(cy, ry, ry + rh)
    dx = cx - nearest_x
    dy = cy - nearest_y
    return (dx * dx + dy * dy) <= (cr * cr)


def slide_circle_against_rects(cx, cy, cr, dx, dy, rects):
    """
    Gerakkan lingkaran (cx,cy,cr) sebesar (dx,dy) dengan sliding collision
    terhadap daftar persegi panjang.

    Return:
        (new_x, new_y)
    """
    # Coba X dulu
    new_x = cx + dx
    blocked_x = False
    for r in rects:
        if circle_rect_collision(new_x, cy, cr, r[0], r[1], r[2], r[3]):
            blocked_x = True
            break
    if blocked_x:
        new_x = cx

    # Coba Y
    new_y = cy + dy
    blocked_y = False
    for r in rects:
        if circle_rect_collision(new_x, new_y, cr, r[0], r[1], r[2], r[3]):
            blocked_y = True
            break
    if blocked_y:
        new_y = cy

    return new_x, new_y
