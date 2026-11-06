import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
#  DUNGEON_GAME.PY - Hunter Assassin 43 Multi-Shape Room Dungeon
#  "DUNGEON SURVIVAL: Bayesian Shadow Ninja"
#  Mata Kuliah: 10S3109 - Kecerdasan Buatan (CERTAN)
#  Topik: Uncertainty (Teorema Bayes & Expected Utility)
# ============================================================

import pygame
import random
import math
import sys

# Import dataset & konfigurasi
from dataset import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GAME_AREA_WIDTH, PANEL_WIDTH, FPS,
    TILE_SIZE, NINJA_CONFIG, MONSTER_STATS, DIFFICULTY_CONFIG,
    UI_CONFIG, GAME_TEXTS, CAMERA_CONFIG,
    # Warna Ninja & Lingkungan
    COLOR_NINJA_BODY, COLOR_NINJA_INNER, COLOR_NINJA_MASK,
    COLOR_NINJA_EYES, COLOR_NINJA_PUPIL, COLOR_NINJA_HEADBAND,
    COLOR_NINJA_TASSEL, COLOR_NINJA_ARMOR, COLOR_NINJA_ARMOR_EDGE,
    COLOR_NINJA_KATANA, COLOR_NINJA_KATANA_EDGE, COLOR_NINJA_SCABBARD,
    # Balok Penutup Hijau Khas Hunter Assassin (Tactical Containers)
    COLOR_CONTAINER, COLOR_CONTAINER_DARK, COLOR_CONTAINER_BORDER, COLOR_CONTAINER_HIGHLIGHT,
    # Warna Monster
    COLOR_GOBLIN, COLOR_GOBLIN_DARK, COLOR_GOBLIN_EYES,
    COLOR_ORC, COLOR_ORC_DARK, COLOR_ORC_EYES,
    COLOR_STALKER, COLOR_STALKER_DARK, COLOR_STALKER_EYES,
    COLOR_WARDEN, COLOR_WARDEN_DARK, COLOR_WARDEN_EYES,
    # Warna Dunia & Portal
    COLOR_FLOOR, COLOR_FLOOR_ALT, COLOR_FLOOR_TILE_LINE,
    COLOR_WALL, COLOR_WALL_BORDER, COLOR_WALL_HIGHLIGHT, COLOR_WALL_SHADOW,
    COLOR_PORTAL_PAD, COLOR_PORTAL_GLOW, COLOR_FOG,
    # Warna UI & FX
    COLOR_HP_BAR, COLOR_HP_BG, COLOR_HP_BORDER, COLOR_GOLD_ICON,
    COLOR_PANEL_BG, COLOR_PANEL_BG2, COLOR_PANEL_BORDER,
    COLOR_PANEL_TEXT, COLOR_PANEL_TITLE, COLOR_PANEL_HIGHLIGHT,
    COLOR_CLAW_MARK, COLOR_DAMAGE_TEXT, COLOR_KILL_TEXT, COLOR_CONFETTI,
    # Probabilitas Bayes
    STAGE_PRIORS, STAGE_PRIORS_HARD, AUDIO_CLUES, THREAT_TYPES,
    CLUE_NAMES, THREAT_NAMES_ID, AUDIO_CONFIG,
)

# Import AI & Geometri
from ai_model import (
    BayesianThreatAnalyzer, ExpectedUtilityAdvisor,
    ShannonEntropyCalculator, SoundSynthesizer,
    CombatAnalyzer, AudioClueGenerator,
    distance, angle_between, normalize_angle, clamp,
    point_in_rect, circle_rect_collision, slide_circle_against_rects
)


# ============================================================
#  FUNGSI BANTU DETEKSI RINTANGAN PANDANGAN (LINE OF SIGHT)
# ============================================================

def line_blocked_by_rect(p1, p2, rx, ry, rw, rh):
    """Cek apakah garis pandang p1-p2 terhalang oleh kotak rintangan rx, ry, rw, rh."""
    min_x, max_x = min(p1[0], p2[0]), max(p1[0], p2[0])
    min_y, max_y = min(p1[1], p2[1]), max(p1[1], p2[1])
    if max_x < rx or min_x > rx + rw or max_y < ry or min_y > ry + rh:
        return False
    for t in (0.2, 0.4, 0.6, 0.8):
        tx = p1[0] + (p2[0] - p1[0]) * t
        ty = p1[1] + (p2[1] - p1[1]) * t
        if rx <= tx <= rx + rw and ry <= ty <= ry + rh:
            return True
    return False


def slerp_angle(current, target, factor):
    """Interpolasi sudut yang halus agar putaran karakter dan monster tidak kaku."""
    diff = normalize_angle(target - current)
    return current + diff * factor


def vec2(x, y):
    return pygame.math.Vector2(x, y)


def render_text(surface, text, pos, size=UI_CONFIG['font_size_normal'], color=COLOR_PANEL_TEXT, bold=False, center=False):
    """Render teks antarmuka HUD dan Panel AI."""
    font = pygame.font.SysFont('segoe ui', size, bold=bold)
    rendered = font.render(str(text), True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(rendered, rect)
    return rect


# ============================================================
#  KELAS: EFEK VISUAL TEMPUR (SLASH ARC, SPARKS, CLAW, DAMAGE TEXT)
# ============================================================

class SlashArcFX:
    """Efek busur tebasan sabit perak-emas saat katana menebas monster."""

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.life = 14
        self.max_life = 14

    def update(self):
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        alpha = int(255 * t)
        radius = int(28 + (1.0 - t) * 16)
        arc_surf = pygame.Surface((radius * 2 + 12, radius * 2 + 12), pygame.SRCALPHA)
        center = (radius + 6, radius + 6)

        points = []
        steps = 12
        start_a = self.angle - 1.1
        end_a = self.angle + 1.1

        # Busur lengkung luar
        for i in range(steps + 1):
            a = start_a + (end_a - start_a) * (i / steps)
            r = radius
            points.append((center[0] + math.cos(a) * r, center[1] + math.sin(a) * r))

        # Busur lengkung dalam (mengecil tajam di ujung)
        for i in range(steps, -1, -1):
            a = start_a + (end_a - start_a) * (i / steps)
            r = radius - 6.5 * math.sin((i / steps) * math.pi)
            points.append((center[0] + math.cos(a) * r, center[1] + math.sin(a) * r))

        if len(points) >= 3:
            # Lapisan emas tajam
            pygame.draw.polygon(arc_surf, (255, 235, 140, alpha), points)
            # Kilatan putih di tengah bilah tebasan
            pygame.draw.polygon(arc_surf, (255, 255, 255, int(alpha * 0.95)), points, 2)

        surf.blit(arc_surf, (int(self.x - radius - 6), int(self.y - radius - 6)))


class SparkParticle:
    """Partikel percikan tajam saat tebasan pedang mengenai monster."""

    def __init__(self, x, y, angle=None):
        self.pos = vec2(x, y)
        spd = random.uniform(2.8, 6.8)
        a = (angle + random.uniform(-0.9, 0.9)) if angle is not None else random.uniform(0, math.pi * 2)
        self.vel = vec2(math.cos(a) * spd, math.sin(a) * spd)
        self.color = random.choice([
            (255, 240, 120), (255, 200, 60), (255, 255, 255), (255, 80, 80)
        ])
        self.life = random.randint(10, 20)
        self.max_life = self.life
        self.size = random.randint(2, 4)

    def update(self):
        self.pos += self.vel
        self.vel *= 0.91
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        alpha = int(255 * t)
        p_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*self.color, alpha), (self.size, self.size), max(1, int(self.size * t)))
        surf.blit(p_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))


class DamageText:
    """Teks melayang saat monster menerima tebasan atau ninja terkena serangan."""

    def __init__(self, x, y, text, color, scale_pop=True):
        self.pos = vec2(x, y)
        self.text = text
        self.color = color
        self.life = CAMERA_CONFIG['damage_text_duration']
        self.max_life = self.life
        self.speed = CAMERA_CONFIG['damage_text_speed']
        self.scale_pop = scale_pop

    def update(self):
        self.pos.y -= self.speed
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        alpha = max(0, min(255, int(255 * t)))
        font_size = 14 if (self.scale_pop and self.life > self.max_life - 6) else 12
        font = pygame.font.SysFont('segoe ui', font_size, bold=True)
        rendered = font.render(self.text, True, self.color)
        rendered.set_alpha(alpha)
        rect = rendered.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        surf.blit(rendered, rect)


class ClawMark:
    """Efek visual 3 goresan cakaran saat monster menyerang pemain dari depan."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = CAMERA_CONFIG['claw_mark_duration']
        self.max_life = self.life

    def update(self):
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        claw_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        for ox in [-12, 0, 12]:
            sp = (16 + ox, 8)
            ep = (48 + ox, 54)
            pygame.draw.line(claw_surf, (*COLOR_CLAW_MARK, alpha), sp, ep, 4)
            pygame.draw.line(claw_surf, (255, 230, 230, alpha), (sp[0]+1, sp[1]+1), (ep[0]-1, ep[1]-1), 2)
        surf.blit(claw_surf, (int(self.x - 32), int(self.y - 32)))


class ConfettiParticle:
    """Partikel confetti berputar untuk selebrasi kemenangan."""

    def __init__(self, x, y):
        self.pos = vec2(x, y)
        self.vel = vec2(random.uniform(-3.0, 3.0), random.uniform(-6.0, -1.0))
        self.color = random.choice(COLOR_CONFETTI)
        self.w = random.randint(6, 11)
        self.h = random.randint(5, 8)
        self.angle = random.uniform(0, 360)
        self.ang_vel = random.uniform(-9, 9)
        self.life = random.randint(120, 240)
        self.max_life = self.life

    def update(self):
        self.pos += self.vel
        self.vel.y += 0.08
        self.vel.x *= 0.99
        self.angle += self.ang_vel
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        p_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        p_surf.fill(self.color)
        rot_surf = pygame.transform.rotate(p_surf, self.angle)
        rect = rot_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        surf.blit(rot_surf, rect)


# ============================================================
#  KELAS: Player (Ninja Hunter Assassin Keren dengan After-Image)
# ============================================================

class Player:
    """Karakter Ninja dengan efek bayangan siluet lari, pedang baja berkilau, dan mata menyala."""

    def __init__(self, x, y, speed_mult=1.0):
        self.pos = vec2(x, y)
        self.radius = NINJA_CONFIG['radius']
        self.base_speed = NINJA_CONFIG['speed']
        self.speed = self.base_speed * speed_mult
        self.hp = NINJA_CONFIG['hp']
        self.max_hp = NINJA_CONFIG['max_hp']
        self.gold = 0
        self.kill_count = 0
        self.facing = -math.pi * 0.5  # Menghadap ke atas
        self.target_facing = self.facing
        self.anim_tassel = 0.0
        self.step_time = 0.0
        self.adjacent_monsters_count = 0
        self.being_attacked = False  # True jika ada monster yang sedang mengejar/mau menyerang
        # Jejak siluet bayangan lari (stealth shadow trail)
        self.trail = []
        self.slash_anim_timer = 0.0  # Timer animasi visual ayunan pedang katana saat menekan SPASI

        # ── SKILL 1: DASH STRIKE (Tekan 1) ──────────────────────────────
        # Dash ke depan + tebasan beruntun instan. Cooldown 2,3 detik.
        self.skill1_active    = False      # Sedang animasi dash
        self.skill1_timer     = 0.0        # Sisa durasi animasi dash
        self.skill1_duration  = 0.38       # Detik durasi animasi dash
        self.skill1_dash_spd  = 520.0      # Kecepatan dash (px/s)
        self.skill1_range     = 70.0       # Jangkauan tebasan (panjang pedang)
        self.skill1_cooldown  = 2.3        # Cooldown 2,3 detik
        self.skill1_cd_timer  = 0.0        # Cooldown tersisa

        # ── SKILL 2: VANISH / MENGHILANG (Tekan 2) ──────────────────────
        # Ninja transparan — monster tidak bisa mendeteksi. Durasi 5 detik.
        # Cooldown 9 detik setelah menghilang. Batal saat menyerang.
        self.skill2_active    = False      # Sedang menghilang
        self.skill2_timer     = 0.0        # Sisa durasi menghilang (maks 5)
        self.skill2_duration  = 5.0
        self.skill2_cooldown  = 9.0
        self.skill2_cd_timer  = 0.0        # Cooldown tersisa

    def apply_difficulty(self, speed_mult):
        self.speed = self.base_speed * speed_mult

    def update_skills(self, dt):
        """Update timer Skill 1 (Dash Strike) dan Skill 2 (Vanish)."""
        # Timer animasi visual tebasan katana
        if self.slash_anim_timer > 0:
            self.slash_anim_timer -= dt
            if self.slash_anim_timer < 0:
                self.slash_anim_timer = 0.0

        # Skill 1: animasi dash
        if self.skill1_active:
            self.skill1_timer -= dt
            if self.skill1_timer <= 0:
                self.skill1_active = False
                self.skill1_timer  = 0.0

        # Skill 1: cooldown (2,3 detik)
        if self.skill1_cd_timer > 0:
            self.skill1_cd_timer -= dt
            if self.skill1_cd_timer < 0:
                self.skill1_cd_timer = 0.0

        # Skill 2: durasi vanish
        if self.skill2_active:
            self.skill2_timer -= dt
            if self.skill2_timer <= 0:
                self.skill2_active = False
                self.skill2_timer  = 0.0
                self.skill2_cd_timer = self.skill2_cooldown  # mulai cooldown

        # Skill 2: cooldown
        if self.skill2_cd_timer > 0:
            self.skill2_cd_timer -= dt
            if self.skill2_cd_timer < 0:
                self.skill2_cd_timer = 0.0

    def cancel_vanish(self):
        """Batalkan Vanish (misal saat menyerang) dan mulai cooldown."""
        if self.skill2_active:
            self.skill2_active = False
            self.skill2_timer = 0.0
            self.skill2_cd_timer = self.skill2_cooldown

    def handle_input(self, keys):
        move = vec2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1

        if move.length_squared() > 0:
            move = move.normalize() * self.speed
            self.target_facing = math.atan2(move.y, move.x)
            self.anim_tassel += 0.45
            self.step_time += 0.3
            # Catat jejak bayangan siluet
            if len(self.trail) == 0 or (self.pos - self.trail[-1][0]).length() > 6:
                self.trail.append((vec2(self.pos.x, self.pos.y), self.facing, 1.0))
                if len(self.trail) > 4:
                    self.trail.pop(0)
        return move

    def update(self, move_vec, wall_rects):
        if move_vec.length_squared() > 0:
            nx, ny = slide_circle_against_rects(
                self.pos.x, self.pos.y, self.radius,
                move_vec.x, move_vec.y, wall_rects
            )
            self.pos.update(nx, ny)

        # Update sisa jejak bayangan
        new_trail = []
        for p, f, life in self.trail:
            life -= 0.12
            if life > 0:
                new_trail.append((p, f, life))
        self.trail = new_trail

        # Putaran arah hadap halus
        self.facing = slerp_angle(self.facing, self.target_facing, 0.3)

    def draw(self, surf, center_override=None, alpha_override=255):
        cx = int(center_override[0]) if center_override else int(self.pos.x)
        cy = int(center_override[1]) if center_override else int(self.pos.y)

        # Efek Vanish: render ke surface sementara lalu apply alpha
        if alpha_override < 255:
            tmp = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
            self._draw_body(tmp, cx, cy, center_override)
            tmp.set_alpha(alpha_override)
            surf.blit(tmp, (0, 0))
            return
        self._draw_body(surf, cx, cy, center_override)

    def _draw_body(self, surf, cx, cy, center_override=None):
        # cx, cy sudah dihitung di draw(), tidak perlu re-compute

        # 1. Jejak Bayangan Siluet Lari (Phantom After-Image)
        if center_override is None:
            for p, f, life in self.trail:
                t_alpha = int(90 * life)
                t_surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(t_surf, (20, 20, 30, t_alpha), (self.radius + 2, self.radius + 2), int(self.radius * 0.9))
                surf.blit(t_surf, (int(p.x - self.radius - 2), int(p.y - self.radius - 2)))

        # 2. Bayangan Lembut Ninja di Bawah Tubuh
        shadow_surf = pygame.Surface((self.radius * 2.3, int(self.radius * 0.75)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), shadow_surf.get_rect())
        surf.blit(shadow_surf, (cx - self.radius * 1.15, cy + int(self.radius * 0.35)))

        # 3. Aura Stealth Berdenyut
        pulse_stealth = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 2.5
        aura_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (40, 60, 90, 45), (self.radius + 5, self.radius + 5), int(self.radius + pulse_stealth))
        surf.blit(aura_surf, (cx - self.radius - 5, cy - self.radius - 5))

        # 4. Katana Baja Mengkilap (Ditebaskan saat menyerang vs Disarungkan di Punggung)
        if self.slash_anim_timer > 0:
            # Pedang sedang diayunkan menebas menyapu ke depan!
            progress = 1.0 - (self.slash_anim_timer / 0.18)
            blade_angle = self.facing - 1.1 + progress * 2.2
            kat_len = self.radius * 2.7
            k_sx = cx + math.cos(blade_angle) * (self.radius * 0.4)
            k_sy = cy + math.sin(blade_angle) * (self.radius * 0.4)
            k_ex = cx + math.cos(blade_angle) * kat_len
            k_ey = cy + math.sin(blade_angle) * kat_len
            # Gagang scabbard & bilah pedang menebas berkilau emas-perak
            pygame.draw.line(surf, (200, 40, 40), (int(cx), int(cy)), (int(k_sx), int(k_sy)), 4)
            pygame.draw.line(surf, (255, 255, 255), (int(k_sx), int(k_sy)), (int(k_ex), int(k_ey)), 3)
            pygame.draw.line(surf, (255, 235, 120), (int(k_sx), int(k_sy)), (int(k_ex), int(k_ey)), 1)
        else:
            scabbard_angle = self.facing + math.pi * 0.82
            kat_len = self.radius * 2.1
            k_sx = cx - math.cos(scabbard_angle) * (self.radius * 0.4)
            k_sy = cy - math.sin(scabbard_angle) * (self.radius * 0.4)
            k_ex = cx + math.cos(scabbard_angle) * kat_len
            k_ey = cy + math.sin(scabbard_angle) * kat_len
            # Gagang scabbard kayu hitam-emas
            pygame.draw.line(surf, (30, 20, 15), (int(k_sx), int(k_sy)), (int(k_ex), int(k_ey)), 4)
            # Bilah baja perak mengkilap
            pygame.draw.line(surf, COLOR_NINJA_KATANA, (int(k_sx), int(k_sy)), (int(k_ex), int(k_ey)), 2)
            pygame.draw.line(surf, (255, 255, 255), (int(k_sx + 1), int(k_sy)), (int(k_ex), int(k_ey)), 1)

        # 5. Tubuh Ninja & Pelindung Bahu Armor
        pygame.draw.circle(surf, COLOR_NINJA_BODY, (cx, cy), self.radius)
        pygame.draw.circle(surf, COLOR_NINJA_INNER, (cx, cy), int(self.radius * 0.78))

        for sign in (-1, 1):
            s_angle = self.facing + sign * math.pi * 0.52
            sx = cx + math.cos(s_angle) * (self.radius * 0.88)
            sy = cy + math.sin(s_angle) * (self.radius * 0.88)
            pygame.draw.circle(surf, COLOR_NINJA_ARMOR, (int(sx), int(sy)), int(self.radius * 0.44))
            pygame.draw.circle(surf, COLOR_NINJA_ARMOR_EDGE, (int(sx), int(sy)), int(self.radius * 0.44), 1)

        # 6. Topeng & Kepala Ninja
        head_radius = int(self.radius * 0.7)
        head_x = cx + math.cos(self.facing) * (self.radius * 0.3)
        head_y = cy + math.sin(self.facing) * (self.radius * 0.3)
        pygame.draw.circle(surf, COLOR_NINJA_MASK, (int(head_x), int(head_y)), head_radius)

        # 7. Ikat Kepala Merah Darah & Rumbai Berkibar
        hb_front_x = head_x + math.cos(self.facing) * (head_radius * 0.4)
        hb_front_y = head_y + math.sin(self.facing) * (head_radius * 0.4)
        pygame.draw.circle(surf, COLOR_NINJA_HEADBAND, (int(hb_front_x), int(hb_front_y)), int(head_radius * 0.58))

        tassel_back_x = cx - math.cos(self.facing) * (self.radius * 0.82)
        tassel_back_y = cy - math.sin(self.facing) * (self.radius * 0.82)
        sway1 = math.sin(self.anim_tassel) * 4.8
        sway2 = math.cos(self.anim_tassel) * 3.8
        t1_end = (int(tassel_back_x - math.cos(self.facing)*10 + sway1), int(tassel_back_y - math.sin(self.facing)*10 + sway2))
        t2_end = (int(tassel_back_x - math.cos(self.facing)*13 - sway2), int(tassel_back_y - math.sin(self.facing)*13 + sway1))
        pygame.draw.line(surf, COLOR_NINJA_TASSEL, (int(tassel_back_x), int(tassel_back_y)), t1_end, 2)
        pygame.draw.line(surf, (255, 60, 60), (int(tassel_back_x), int(tassel_back_y)), t2_end, 2)

        # 8. Mata Ninja Menyala Cyan
        eye_dist = head_radius * 0.44
        eye_fwd = head_radius * 0.48
        left_eye_x = head_x + math.cos(self.facing) * eye_fwd + math.cos(self.facing - math.pi*0.5) * eye_dist
        left_eye_y = head_y + math.sin(self.facing) * eye_fwd + math.sin(self.facing - math.pi*0.5) * eye_dist
        right_eye_x = head_x + math.cos(self.facing) * eye_fwd + math.cos(self.facing + math.pi*0.5) * eye_dist
        right_eye_y = head_y + math.sin(self.facing) * eye_fwd + math.sin(self.facing + math.pi*0.5) * eye_dist
        # Kilauan mata
        pygame.draw.circle(surf, (120, 230, 255), (int(left_eye_x), int(left_eye_y)), 3)
        pygame.draw.circle(surf, (120, 230, 255), (int(right_eye_x), int(right_eye_y)), 3)
        pygame.draw.circle(surf, (255, 255, 255), (int(left_eye_x), int(left_eye_y)), 1)
        pygame.draw.circle(surf, (255, 255, 255), (int(right_eye_x), int(right_eye_y)), 1)

        # 9. Lencana Angka di Atas Kepala (Minesweeper Percept)
        if center_override is None:
            badge_radius = 8
            badge_x = cx
            badge_y = cy - self.radius - 14

            count = self.adjacent_monsters_count
            if count == 0:
                badge_bg = (35, 140, 60)
                badge_border = (80, 240, 120)
            elif count == 1:
                badge_bg = (180, 140, 20)
                badge_border = (255, 220, 60)
            elif count == 2:
                badge_bg = (190, 80, 20)
                badge_border = (255, 130, 40)
            else:
                badge_bg = (180, 25, 25)
                badge_border = (255, 60, 60)

            pygame.draw.circle(surf, badge_bg, (badge_x, badge_y), badge_radius)
            pygame.draw.circle(surf, badge_border, (badge_x, badge_y), badge_radius, 1)

            font_badge = pygame.font.SysFont('segoe ui', 11, bold=True)
            txt_surf = font_badge.render(str(count), True, (255, 255, 255))
            txt_r = txt_surf.get_rect(center=(badge_x, badge_y))
            surf.blit(txt_surf, txt_r)

            # 10. TANDA SERU BAHAYA DI DEKAT KARAKTER (Saat Monster Mau Menyerang Kita)
            if self.being_attacked:
                ticks = pygame.time.get_ticks()
                bounce = abs(math.sin(ticks * 0.012)) * 4.0
                alert_x = cx + self.radius + 6
                alert_y = int(cy - self.radius - 16 - bounce)

                # Balon dialog tanda seru merah menyala
                bubble_w, bubble_h = 16, 20
                bubble_rect = pygame.Rect(alert_x - bubble_w // 2, alert_y - bubble_h // 2, bubble_w, bubble_h)
                # Warna berkedip antara merah pekat dan kuning menyala
                flash_col = (255, 30, 30) if (ticks // 150) % 2 == 0 else (255, 180, 0)
                pygame.draw.rect(surf, flash_col, bubble_rect, border_radius=4)
                pygame.draw.rect(surf, (255, 255, 255), bubble_rect, 1, border_radius=4)

                # Teks tanda seru tebal
                font_excl = pygame.font.SysFont('segoe ui', 14, bold=True)
                excl_surf = font_excl.render("!", True, (255, 255, 255))
                excl_r = excl_surf.get_rect(center=bubble_rect.center)
                surf.blit(excl_surf, excl_r)

                # Cincin bahaya merah berdenyut di sekitar kaki ninja
                danger_pulse = abs(math.sin(ticks * 0.01)) * 5.0
                ring_r = int(self.radius + 6 + danger_pulse)
                ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                ring_alpha = max(0, min(255, int(160 * (1.0 - (danger_pulse / 5.0)))))
                pygame.draw.circle(ring_surf, (255, 40, 40, ring_alpha), (ring_r + 2, ring_r + 2), ring_r, 2)
                surf.blit(ring_surf, (cx - ring_r - 2, cy - ring_r - 2))


# ============================================================
#  KELAS: Monster (Musuh Buas Bernapas dengan Aura Khas)
# ============================================================

class Monster:
    """Monster buas dengan animasi bernapas, aura ancaman dinamis, dan bayangan ganda."""

    def __init__(self, monster_type, x, y, room_rects, all_walls, room_containers, diff_config=None):
        self.type_id = monster_type
        self.stats = MONSTER_STATS[monster_type]
        self.pos = vec2(x, y)
        self.radius = self.stats['radius']
        self.tier = self.stats['tier']
        self.facing = random.uniform(0, 2 * math.pi)
        self.target_facing = self.facing
        self.state = 'patrol'

        speed_mult = diff_config['monster_speed_mult'] if diff_config else 1.0
        chase_mult = diff_config['monster_chase_mult'] if diff_config else 1.0
        dmg_mult = diff_config['monster_damage_mult'] if diff_config else 1.0
        cd_mult = diff_config['monster_cooldown_mult'] if diff_config else 1.0
        det_mult = diff_config['detection_mult'] if diff_config else 1.0

        self.speed = self.stats['speed'] * speed_mult
        self.chase_speed = self.stats['chase_speed'] * chase_mult
        self.damage = int(self.stats['damage'] * dmg_mult)
        self.attack_cooldown = self.stats['attack_cooldown'] * cd_mult
        self.detection_range = self.stats['detection_range'] * det_mult
        self.vision_angle = self.stats['vision_angle']

        # 3 Hit System
        self.hits_to_kill = 3
        self.hits_remaining = 3
        self.hit_invulnerable_timer = 0.0
        self.cooldown_timer = 0.0

        self.room_rects = room_rects
        self.all_walls = all_walls
        self.room_containers = room_containers
        self.target_patrol = self._pick_patrol_point()
        self.patrol_wait = 0.0
        self.anim_time = random.uniform(0, 10.0)
        self.was_chasing = False  # Status sebelumnya untuk memicu suara tanda seru alert

    def apply_difficulty(self, diff_config):
        self.speed = self.stats['speed'] * diff_config['monster_speed_mult']
        self.chase_speed = self.stats['chase_speed'] * diff_config['monster_chase_mult']
        self.damage = int(self.stats['damage'] * diff_config['monster_damage_mult'])
        self.attack_cooldown = self.stats['attack_cooldown'] * diff_config['monster_cooldown_mult']
        self.detection_range = self.stats['detection_range'] * diff_config['detection_mult']

    def _pick_patrol_point(self):
        rect = random.choice(self.room_rects)
        pad = self.radius + 8
        for _ in range(25):
            tx = random.uniform(rect.left + pad, rect.right - pad)
            ty = random.uniform(rect.top + pad, rect.bottom - pad)
            blocked = False
            # Cek hanya dinding — monster dan box bisa berdekatan (box bisa dikelilingi)
            for w in self.all_walls:
                if point_in_rect(tx, ty, w[0], w[1], w[2], w[3]):
                    blocked = True
                    break
            if not blocked:
                return vec2(tx, ty)
        return vec2(self.pos.x, self.pos.y)

    def is_point_in_room(self, px, py):
        return any(r.collidepoint(px, py) for r in self.room_rects)

    def can_see_player(self, player):
        if not self.is_point_in_room(player.pos.x, player.pos.y):
            return False

        dist = distance((self.pos.x, self.pos.y), (player.pos.x, player.pos.y))
        if dist > self.detection_range:
            return False

        angle_to_ninja = math.atan2(player.pos.y - self.pos.y, player.pos.x - self.pos.x)
        diff_angle = abs(normalize_angle(angle_to_ninja - self.facing))
        if diff_angle > math.radians(65):
            return False

        p1 = (self.pos.x, self.pos.y)
        p2 = (player.pos.x, player.pos.y)
        for b in self.room_containers:
            if line_blocked_by_rect(p1, p2, b[0], b[1], b[2], b[3]):
                return False

        return True

    def update(self, player, dt, sounds, damage_texts, claw_marks, is_player_in_same_room):
        if self.state == 'dead':
            return

        self.anim_time += dt

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

        if self.hit_invulnerable_timer > 0:
            self.hit_invulnerable_timer -= dt

        if not is_player_in_same_room:
            self.state = 'patrol'

        sees_ninja = is_player_in_same_room and self.can_see_player(player)

        if sees_ninja:
            if not self.was_chasing:
                if 'alert' in sounds:
                    sounds['alert'].play()
            self.state = 'chase'
            self.was_chasing = True
            self.target_facing = math.atan2(player.pos.y - self.pos.y, player.pos.x - self.pos.x)
            move_dir = vec2(math.cos(self.facing), math.sin(self.facing)) * (self.chase_speed * 60 * dt)
        else:
            self.state = 'patrol'
            self.was_chasing = False
            dist_to_target = (self.target_patrol - self.pos).length()
            if dist_to_target < 14 or self.patrol_wait > 0:
                if self.patrol_wait <= 0:
                    self.patrol_wait = random.uniform(0.6, 1.6)
                else:
                    self.patrol_wait -= dt
                    if self.patrol_wait <= 0:
                        self.target_patrol = self._pick_patrol_point()
                move_dir = vec2(0, 0)
            else:
                self.target_facing = math.atan2(self.target_patrol.y - self.pos.y, self.target_patrol.x - self.pos.x)
                move_dir = vec2(math.cos(self.facing), math.sin(self.facing)) * (self.speed * 60 * dt)

        self.facing = slerp_angle(self.facing, self.target_facing, 0.25)

        if move_dir.length_squared() > 0:
            nx, ny = slide_circle_against_rects(
                self.pos.x, self.pos.y, self.radius,
                move_dir.x, move_dir.y, self.all_walls
            )
            if self.is_point_in_room(nx, ny):
                self.pos.update(nx, ny)
            else:
                self.target_patrol = self._pick_patrol_point()

            # Push-out monster dari box pelindung agar bisa melingkarinya
            mr = self.radius
            mx2, my2 = self.pos.x, self.pos.y
            for b in self.room_containers:
                bx2, by2, bw2, bh2 = b
                nearest_x = max(bx2, min(mx2, bx2 + bw2))
                nearest_y = max(by2, min(my2, by2 + bh2))
                dist_x = mx2 - nearest_x
                dist_y = my2 - nearest_y
                dist2 = dist_x * dist_x + dist_y * dist_y
                if dist2 < mr * mr and dist2 > 0.0001:
                    dist = math.sqrt(dist2)
                    overlap = mr - dist
                    self.pos.x += (dist_x / dist) * overlap
                    self.pos.y += (dist_y / dist) * overlap
                    mx2, my2 = self.pos.x, self.pos.y

    def draw(self, surf):
        if self.state == 'dead':
            return

        cx = int(self.pos.x)
        cy = int(self.pos.y)

        # Efek pernapasan halus (breathing scale)
        breath = math.sin(self.anim_time * 5.0) * 0.8
        cur_r = int(self.radius + breath)

        # 1. Bayangan Ganda Bertingkat (Dual-layer Soft Shadow)
        shadow_w = int(self.radius * 2.4)
        shadow_h = int(self.radius * 0.85)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        # Lapisan luar halus
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 75), shadow_surf.get_rect())
        # Inti pekat
        inner_r = shadow_surf.get_rect().inflate(-4, -2)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), inner_r)
        surf.blit(shadow_surf, (cx - shadow_w // 2, cy + int(self.radius * 0.38)))

        # 2. Aura Khas Sesuai Tier Monster
        aura_pulse = abs(math.sin(self.anim_time * 4.0)) * 3.0
        aura_sz = int(cur_r * 2 + 14 + aura_pulse)
        aura_surf = pygame.Surface((aura_sz, aura_sz), pygame.SRCALPHA)
        aura_center = (aura_sz // 2, aura_sz // 2)

        if self.tier == 1:
            # Goblin: Aura asam beracun hijau
            pygame.draw.circle(aura_surf, (50, 160, 40, 35), aura_center, int(cur_r + aura_pulse))
        elif self.tier == 2:
            # Orc: Aura darah oranye-merah
            pygame.draw.circle(aura_surf, (200, 90, 30, 40), aura_center, int(cur_r + aura_pulse))
        elif self.tier == 3:
            # Shadow Stalker: Aura bayangan ungu mistis
            pygame.draw.circle(aura_surf, (150, 30, 190, 50), aura_center, int(cur_r + aura_pulse))
        else:
            # Warden: Aura magma merah menyala
            pygame.draw.circle(aura_surf, (230, 40, 30, 55), aura_center, int(cur_r + aura_pulse))

        surf.blit(aura_surf, (cx - aura_sz // 2, cy - aura_sz // 2))

        # 3. Indikator HP 3 Pips Elegan dengan Bingkai Logam
        pip_w = 7
        pip_spacing = 3
        total_pips_w = self.hits_to_kill * pip_w + (self.hits_to_kill - 1) * pip_spacing
        start_pip_x = cx - total_pips_w // 2
        pip_y = cy - self.radius - 11

        # Background bar
        bg_bar = pygame.Rect(start_pip_x - 2, pip_y - 2, total_pips_w + 4, 8)
        pygame.draw.rect(surf, (20, 20, 28), bg_bar, border_radius=2)
        pygame.draw.rect(surf, (60, 60, 80), bg_bar, 1, border_radius=2)

        for i in range(self.hits_to_kill):
            px = start_pip_x + i * (pip_w + pip_spacing)
            if i < self.hits_remaining:
                pip_col = (255, 60, 60) if self.hits_remaining == 1 else ((255, 200, 50) if self.hits_remaining == 2 else (60, 230, 90))
                pygame.draw.rect(surf, pip_col, (px, pip_y, pip_w, 4), border_radius=1)
            else:
                pygame.draw.rect(surf, (45, 45, 55), (px, pip_y, pip_w, 4), border_radius=1)

        # 4. Gambar Tubuh Monster Sesuai Tier
        if self.tier == 1:
            pygame.draw.circle(surf, COLOR_GOBLIN_DARK, (cx, cy), cur_r)
            pygame.draw.circle(surf, COLOR_GOBLIN, (cx, cy), int(cur_r * 0.85))
            for sign in (-1, 1):
                ear_angle = self.facing + sign * math.pi * 0.62
                tip = (int(cx + math.cos(ear_angle) * (cur_r * 1.55)), int(cy + math.sin(ear_angle) * (cur_r * 1.55)))
                base1 = (int(cx + math.cos(ear_angle - 0.3) * (cur_r * 0.7)), int(cy + math.sin(ear_angle - 0.3) * (cur_r * 0.7)))
                base2 = (int(cx + math.cos(ear_angle + 0.3) * (cur_r * 0.7)), int(cy + math.sin(ear_angle + 0.3) * (cur_r * 0.7)))
                pygame.draw.polygon(surf, COLOR_GOBLIN, [tip, base1, base2])
                eye_a = self.facing + sign * 0.4
                pygame.draw.circle(surf, COLOR_GOBLIN_EYES, (int(cx + math.cos(eye_a)*(cur_r*0.6)), int(cy + math.sin(eye_a)*(cur_r*0.6))), 2)

        elif self.tier == 2:
            pygame.draw.circle(surf, COLOR_ORC_DARK, (cx, cy), cur_r)
            pygame.draw.circle(surf, COLOR_ORC, (cx, cy), int(cur_r * 0.88))
            for sign in (-1, 1):
                p_angle = self.facing + sign * math.pi * 0.55
                px = int(cx + math.cos(p_angle) * (cur_r * 0.95))
                py = int(cy + math.sin(p_angle) * (cur_r * 0.95))
                pygame.draw.circle(surf, COLOR_ORC_DARK, (px, py), int(cur_r * 0.46))
                t_angle = self.facing + sign * 0.35
                pygame.draw.circle(surf, (245, 245, 220), (int(cx + math.cos(t_angle)*(cur_r*1.18)), int(cy + math.sin(t_angle)*(cur_r*1.18))), 3)
                eye_a = self.facing + sign * 0.38
                pygame.draw.circle(surf, COLOR_ORC_EYES, (int(cx + math.cos(eye_a)*(cur_r*0.65)), int(cy + math.sin(eye_a)*(cur_r*0.65))), 3)

        elif self.tier == 3:
            pygame.draw.circle(surf, COLOR_STALKER_DARK, (cx, cy), cur_r)
            pygame.draw.circle(surf, COLOR_STALKER, (cx, cy), int(cur_r * 0.85))
            for sign in (-1, 1):
                h_angle = self.facing + sign * math.pi * 0.72
                tip = (int(cx + math.cos(h_angle) * (cur_r * 1.65)), int(cy + math.sin(h_angle) * (cur_r * 1.65)))
                pygame.draw.line(surf, (40, 10, 60), (cx, cy), tip, 4)
            for offset_a in [-0.55, -0.22, 0.22, 0.55]:
                eye_a = self.facing + offset_a
                pygame.draw.circle(surf, COLOR_STALKER_EYES, (int(cx + math.cos(eye_a)*(cur_r*0.7)), int(cy + math.sin(eye_a)*(cur_r*0.7))), 2)

        else:
            pygame.draw.circle(surf, COLOR_WARDEN_DARK, (cx, cy), cur_r)
            pygame.draw.circle(surf, COLOR_WARDEN, (cx, cy), int(cur_r * 0.85))
            for sign in (-1, 1):
                h_angle = self.facing + sign * math.pi * 0.65
                tip = (int(cx + math.cos(h_angle) * (cur_r * 1.8)), int(cy + math.sin(h_angle) * (cur_r * 1.8)))
                pygame.draw.line(surf, (25, 5, 5), (cx, cy), tip, 6)
                pygame.draw.line(surf, (220, 40, 40), (cx, cy), tip, 2)
                eye_a = self.facing + sign * 0.35
                pygame.draw.circle(surf, COLOR_WARDEN_EYES, (int(cx + math.cos(eye_a)*(cur_r*0.6)), int(cy + math.sin(eye_a)*(cur_r*0.6))), 4)
                pygame.draw.circle(surf, (255, 240, 120), (int(cx + math.cos(eye_a)*(cur_r*0.6)), int(cy + math.sin(eye_a)*(cur_r*0.6))), 2)

        # 5. TANDA SERU & PERISAI KEBAL DI ATAS KEPALA MONSTER SAAT MENYERANG KITA
        if self.state == 'chase':
            ticks = pygame.time.get_ticks()
            # Cincin perisai amarah kebal di sekeliling tubuh monster
            shield_pulse = abs(math.sin(ticks * 0.012)) * 4.0
            s_radius = int(cur_r + 6 + shield_pulse)
            s_surf = pygame.Surface((s_radius * 2 + 4, s_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s_surf, (255, 40, 40, 90), (s_radius + 2, s_radius + 2), s_radius, 2)
            pygame.draw.circle(s_surf, (255, 200, 50, 60), (s_radius + 2, s_radius + 2), max(1, s_radius - 2), 1)
            surf.blit(s_surf, (cx - s_radius - 2, cy - s_radius - 2))

            # Balon tanda seru merah menyala
            m_bounce = abs(math.sin(ticks * 0.014)) * 3.0
            m_alert_y = int(cy - self.radius - 22 - m_bounce)
            m_bubble = pygame.Rect(cx - 7, m_alert_y - 9, 14, 18)
            m_flash = (255, 30, 30) if (ticks // 140) % 2 == 0 else (255, 170, 0)
            pygame.draw.rect(surf, m_flash, m_bubble, border_radius=4)
            pygame.draw.rect(surf, (255, 255, 255), m_bubble, 1, border_radius=4)
            font_m_excl = pygame.font.SysFont('segoe ui', 13, bold=True)
            m_excl_s = font_m_excl.render("!", True, (255, 255, 255))
            surf.blit(m_excl_s, m_excl_s.get_rect(center=m_bubble.center))

            # Badge status KEBAL di atas tanda seru
            badge_k = pygame.Rect(cx - 19, m_alert_y - 20, 38, 11)
            pygame.draw.rect(surf, (30, 10, 10), badge_k, border_radius=2)
            pygame.draw.rect(surf, (255, 60, 60), badge_k, 1, border_radius=2)
            font_kb = pygame.font.SysFont('segoe ui', 8, bold=True)
            txt_kb = font_kb.render("KEBAL!", True, (255, 220, 80))
            surf.blit(txt_kb, txt_kb.get_rect(center=badge_k.center))


# ============================================================
#  KELAS: MultiShapeRoomGridMap (Lantai Menyatu Tanpa Garis Pemisah)
# ============================================================

class MultiShapeRoomGridMap:
    """Peta 43 Ruangan Beragam Bentuk dengan Lantai Menyatu Sempurna Tanpa Garis Salib Hitam."""

    def __init__(self, difficulty='NORMAL'):
        self.difficulty = difficulty
        self.cols = 8
        self.rows = 8
        self.margin_x = 16
        self.margin_y = 16
        self.grid_w = 848
        self.grid_h = 768
        self.cell_w = self.grid_w // self.cols   # 106 px
        self.cell_h = self.grid_h // self.rows   # 96 px
        self.wall_t = 6
        self.door_w = 38

        self.analyzer = BayesianThreatAnalyzer()
        self.advisor = ExpectedUtilityAdvisor()
        self.entropy_calc = ShannonEntropyCalculator()
        self.clue_generator = AudioClueGenerator()
        self.synth = SoundSynthesizer()

        self.rooms_info = {}
        self.monsters = {}
        self.room_adj = {}
        self.cell_to_room = [[None for _ in range(self.rows)] for _ in range(self.cols)]
        self.walls = []
        self.containers = []
        self.room_containers = {}

        self._build_multi_shape_layout()
        self._setup_safe_path_and_monsters()

    def _build_multi_shape_layout(self):
        """Bentuk partisi 43 ruangan dengan beragam bentuk dan lantai menyatu mulus."""
        grid = self.cell_to_room
        rooms_list = []

        # 1. Ruangan Berbentuk L (3 subcells siku-siku)
        l_shapes = [
            [(0, 0), (1, 0), (0, 1)],         # Kiri atas
            [(6, 0), (7, 0), (7, 1)],         # Kanan atas
            [(0, 6), (0, 7), (1, 7)],         # Kiri bawah
            [(7, 6), (7, 7), (6, 7)],         # Kanan bawah
        ]
        for cells in l_shapes:
            if all(grid[c][r] is None for c, r in cells):
                rid = len(rooms_list)
                rooms_list.append({'id': rid, 'type': 'l_shape', 'cells': cells})
                for c, r in cells:
                    grid[c][r] = rid

        # 2. Ruangan Aula Besar (2x2 subcells) di tengah labirin
        big_aula = [(3, 3), (4, 3), (3, 4), (4, 4)]
        if all(grid[c][r] is None for c, r in big_aula):
            rid = len(rooms_list)
            rooms_list.append({'id': rid, 'type': 'big', 'cells': big_aula})
            for c, r in big_aula:
                grid[c][r] = rid

        # 3. Ruangan Persegi Panjang & Bilik Tunggal
        pairs_count = 0
        max_pairs = 10
        for r in range(self.rows):
            for c in range(self.cols):
                if grid[c][r] is None:
                    if pairs_count < max_pairs:
                        if (c + r) % 2 == 0 and c + 1 < self.cols and grid[c+1][r] is None:
                            cells = [(c, r), (c+1, r)]
                            rid = len(rooms_list)
                            rooms_list.append({'id': rid, 'type': 'h_rect', 'cells': cells})
                            for cx, rx in cells:
                                grid[cx][rx] = rid
                            pairs_count += 1
                            continue
                        elif r + 1 < self.rows and grid[c][r+1] is None:
                            cells = [(c, r), (c, r+1)]
                            rid = len(rooms_list)
                            rooms_list.append({'id': rid, 'type': 'v_rect', 'cells': cells})
                            for cx, rx in cells:
                                grid[cx][rx] = rid
                            pairs_count += 1
                            continue

                    cells = [(c, r)]
                    rid = len(rooms_list)
                    rooms_list.append({'id': rid, 'type': 'single', 'cells': cells})
                    grid[c][r] = rid

        self.total_rooms = len(rooms_list)
        self.room_adj = {r['id']: set() for r in rooms_list}

        mx, my = self.margin_x, self.margin_y
        gw, gh = self.grid_w, self.grid_h
        wt = self.wall_t
        dw = self.door_w
        cw, ch = self.cell_w, self.cell_h

        # Dinding tepi luar dungeon
        self.walls.append((mx - wt, my - wt, gw + 2*wt, wt))
        self.walls.append((mx - wt, my + gh, gw + 2*wt, wt))
        self.walls.append((mx - wt, my - wt, wt, gh + 2*wt))
        self.walls.append((mx + gw, my - wt, wt, gh + 2*wt))

        # Batas vertikal kolom (hanya buat dinding jika memisahkan ruangan berbeda!)
        for c in range(self.cols - 1):
            wx = mx + (c + 1) * cw - wt // 2
            for r in range(self.rows):
                r1 = grid[c][r]
                r2 = grid[c + 1][r]
                if r1 != r2:
                    self.room_adj[r1].add(r2)
                    self.room_adj[r2].add(r1)
                    sy = my + r * ch
                    ey = sy + ch
                    mid_y = (sy + ey) // 2
                    top_h = (mid_y - dw // 2) - sy
                    bot_y = mid_y + dw // 2
                    bot_h = ey - bot_y
                    if top_h > 0:
                        self.walls.append((wx, sy, wt, top_h))
                    if bot_h > 0:
                        self.walls.append((wx, bot_y, wt, bot_h))

        # Batas horizontal baris (hanya buat dinding jika memisahkan ruangan berbeda!)
        for r in range(self.rows - 1):
            wy = my + (r + 1) * ch - wt // 2
            for c in range(self.cols):
                r1 = grid[c][r]
                r2 = grid[c][r + 1]
                if r1 != r2:
                    self.room_adj[r1].add(r2)
                    self.room_adj[r2].add(r1)
                    sx = mx + c * cw
                    ex = sx + cw
                    mid_x = (sx + ex) // 2
                    left_w = (mid_x - dw // 2) - sx
                    right_x = mid_x + dw // 2
                    right_w = ex - right_x
                    if left_w > 0:
                        self.walls.append((sx, wy, left_w, wt))
                    if right_w > 0:
                        self.walls.append((right_x, wy, right_w, wt))

        # 4. Bangun Rect Lantai
        # KUNCI UTAMA: Untuk ruangan yang terdiri dari > 1 blok, batas dalam ANTAR CELL MENYATU PENUH (tidak ada celah hitam salib!)
        # Box pelindung TIDAK ditempatkan di sini — akan ditempatkan di reseed_monsters()
        # hanya di ruangan yang benar-benar ada monsternya, di TENGAH ruangan.

        for rm in rooms_list:
            rid = rm['id']
            self.room_containers[rid] = []
            rects = []

            for idx, (c, r) in enumerate(rm['cells']):
                rx = mx + c * cw
                ry = my + r * ch

                # Cek apakah tetangga (kiri, kanan, atas, bawah) adalah ruangan yang SAMA
                has_left_same = (c > 0 and grid[c-1][r] == rid)
                has_right_same = (c + 1 < self.cols and grid[c+1][r] == rid)
                has_top_same = (r > 0 and grid[c][r-1] == rid)
                has_bottom_same = (r + 1 < self.rows and grid[c][r+1] == rid)

                # Jika bertetangga dengan sel dalam ruangan yang SAMA, rentangkan sampai batas penuh!
                x1 = rx if has_left_same else (rx + wt)
                x2 = (rx + cw) if has_right_same else (rx + cw - wt)
                y1 = ry if has_top_same else (ry + wt)
                y2 = (ry + ch) if has_bottom_same else (ry + ch - wt)

                rects.append(pygame.Rect(x1, y1, x2 - x1, y2 - y1))

            avg_x = sum(r.centerx for r in rects) / len(rects)
            avg_y = sum(r.centery for r in rects) / len(rects)
            avg_r = sum(c_r[1] for c_r in rm['cells']) / len(rm['cells'])
            depth = max(1, min(5, int(6 - (avg_r * 5 / self.rows))))

            self.rooms_info[rid] = {
                'id': rid,
                'type': rm['type'],
                'cells': rm['cells'],
                'rects': rects,
                'center': (avg_x, avg_y),
                'depth': depth,
                'explored': False,
                'is_goal': False,
                'monster_type': None,
                'clue': 'silence',
            }

        # collision_rects untuk PLAYER & MONSTER: hanya dinding, BUKAN box pelindung
        # Sehingga player dan monster bisa MELINGKARI box dari semua sisi (walk-around)
        # Box tetap memblok pandangan monster (line-of-sight) via room_containers
        # Box ditempatkan di reseed_monsters() — hanya ruangan bermonster yang dapat box
        self.collision_rects = list(self.walls)

    def get_safe_spawn_point(self, room_id, radius=11):
        """Cari titik spawn di dalam ruangan yang 100% bebas dari dinding (box boleh dekat, player bisa melingkarinya)."""
        info = self.rooms_info[room_id]
        best_pt = None
        best_dist = -1
        for rect in info['rects']:
            for fx in (0.3, 0.5, 0.7):
                for fy in (0.3, 0.5, 0.7):
                    tx = rect.left + rect.width * fx
                    ty = rect.top + rect.height * fy
                    min_d = 999.0
                    collided = False
                    # Cek hanya dinding (bukan box) untuk spawn
                    for obs in self.collision_rects:
                        ox, oy, ow, oh = obs
                        cx = max(ox, min(tx, ox + ow))
                        cy = max(oy, min(ty, oy + oh))
                        d = math.hypot(tx - cx, ty - cy)
                        if d < radius + 4:
                            collided = True
                            break
                        if d < min_d:
                            min_d = d
                    if not collided and min_d > best_dist:
                        best_dist = min_d
                        best_pt = (tx, ty)
        if best_pt:
            return best_pt
        return info['center']

    def _generate_tricky_safe_path(self, start_id, goal_id, min_length=12):
        """Menghasilkan rute jalur aman yang berliku-liku (tricky zig-zag) agar tidak mudah ditebak."""
        for attempt in range(80):
            flip = (attempt % 2 == 0)
            wp1_cands = [rid for rid, r in self.rooms_info.items() if r['cells'][0][1] in (5, 6) and ((r['cells'][0][0] <= 2) if flip else (r['cells'][0][0] >= 5))]
            wp2_cands = [rid for rid, r in self.rooms_info.items() if r['cells'][0][1] in (3, 4) and ((r['cells'][0][0] >= 5) if flip else (r['cells'][0][0] <= 2))]
            wp3_cands = [rid for rid, r in self.rooms_info.items() if r['cells'][0][1] in (1, 2) and ((r['cells'][0][0] <= 3) if flip else (r['cells'][0][0] >= 4))]

            if not wp1_cands or not wp2_cands or not wp3_cands:
                continue

            wp1 = random.choice(wp1_cands)
            wp2 = random.choice(wp2_cands)
            wp3 = random.choice(wp3_cands)

            waypoints = [start_id, wp1, wp2, wp3, goal_id]
            full_path = [start_id]
            success = True

            for i in range(len(waypoints) - 1):
                src, dst = waypoints[i], waypoints[i+1]
                q = [[src]]
                v = {src}
                sub = None
                while q:
                    p = q.pop(0)
                    n = p[-1]
                    if n == dst:
                        sub = p
                        break
                    nbrs = list(self.room_adj[n])
                    random.shuffle(nbrs)
                    for nxt in nbrs:
                        if nxt not in v:
                            v.add(nxt)
                            q.append(p + [nxt])
                if not sub:
                    success = False
                    break
                full_path.extend(sub[1:])

            if success and len(set(full_path)) >= min_length:
                return set(full_path)

        # Fallback jika gagal
        q = [[start_id]]
        v = {start_id}
        while q:
            p = q.pop(0)
            n = p[-1]
            if n == goal_id:
                return set(p)
            for nxt in self.room_adj[n]:
                if nxt not in v:
                    v.add(nxt)
                    q.append(p + [nxt])
        return {start_id, goal_id}

    def _setup_safe_path_and_monsters(self):
        """Tentukan Start, Goal (Finish selalu nampak), Jalur Kosong Berkelok Rumit, dan monster."""
        self.start_room_id = self.cell_to_room[3][7]
        self.goal_room_id = self.cell_to_room[4][0]

        self.rooms_info[self.goal_room_id]['is_goal'] = True
        self.rooms_info[self.start_room_id]['explored'] = True

        # Jalur Berkelok Sulit Ditebak (Tricky Meandering Labyrinth)
        self.safe_path = self._generate_tricky_safe_path(self.start_room_id, self.goal_room_id)

        # Portal di tengah ruangan Finish
        goal_cx, goal_cy = self.rooms_info[self.goal_room_id]['center']
        self.portal_rect = pygame.Rect(int(goal_cx - 20), int(goal_cy - 20), 40, 40)
        self.portal_anim = 0.0

        self.reseed_monsters()

    def reseed_monsters(self):
        """Menata ulang monster saat game mulai atau saat mode kesulitan (NORMAL / HARD) diganti."""
        is_hard = (self.difficulty == 'HARD')
        diff_cfg = DIFFICULTY_CONFIG[self.difficulty]

        # Reset semua containers agar tidak double saat reseed
        self.containers.clear()
        for rid in self.room_containers:
            self.room_containers[rid] = []

        for rid, info in self.rooms_info.items():
            # JALUR KOSONG AMAN: Ruangan start, goal, dan safe path selalu 100% BEBAS MONSTER
            if rid in self.safe_path or rid == self.goal_room_id or rid == self.start_room_id:
                m_type = None
            else:
                priors_source = STAGE_PRIORS_HARD if is_hard else STAGE_PRIORS
                priors = priors_source.get(info['depth'], priors_source[5])
                roll = random.random()
                cumul = 0.0
                m_type = None
                for t in THREAT_TYPES:
                    cumul += priors[t]
                    if roll <= cumul:
                        m_type = None if t == 'safe' else t
                        break

            clue = self.clue_generator.generate_clue(m_type)
            info['monster_type'] = m_type
            info['clue'] = clue

            if m_type:
                # Tempatkan 1 BOX DI TENGAH ruangan (hanya ruangan bermonster)
                # Box cukup 1 per ruangan agar bisa dikelilingi dari semua sisi
                cx, cy = info['center']
                box_w, box_h = 30, 22
                bx = int(cx - box_w // 2)
                by = int(cy - box_h // 2)
                # Pastikan box tidak keluar batas ruangan (clamp ke rect terluas)
                union_rect = info['rects'][0].copy()
                for rr in info['rects'][1:]:
                    union_rect = union_rect.union(rr)
                pad = 12
                bx = clamp(bx, union_rect.left + pad, union_rect.right - box_w - pad)
                by = clamp(by, union_rect.top + pad, union_rect.bottom - box_h - pad)
                box_rect = (bx, by, box_w, box_h)
                self.containers.append(box_rect)
                self.room_containers[rid] = [box_rect]

                mx_pos, my_pos = self.get_safe_spawn_point(rid, radius=14)
                self.monsters[rid] = Monster(
                    m_type, mx_pos, my_pos,
                    info['rects'], self.collision_rects,
                    self.room_containers[rid], diff_cfg
                )
            else:
                # Ruangan tanpa monster = KOSONG, tidak ada box
                self.room_containers[rid] = []
                self.monsters[rid] = None

    def get_room_id_at(self, px, py):
        c = int((px - self.margin_x) // self.cell_w)
        r = int((py - self.margin_y) // self.cell_h)
        c = clamp(c, 0, self.cols - 1)
        r = clamp(r, 0, self.rows - 1)
        return self.cell_to_room[c][r]

    def get_adjacent_rooms(self, curr_room_id):
        curr_center = self.rooms_info[curr_room_id]['center']
        neighbors = []
        for n_id in sorted(list(self.room_adj[curr_room_id])):
            n_center = self.rooms_info[n_id]['center']
            dx = n_center[0] - curr_center[0]
            dy = n_center[1] - curr_center[1]
            if abs(dx) > abs(dy):
                dir_label = "Timur" if dx > 0 else "Barat"
            else:
                dir_label = "Selatan" if dy > 0 else "Utara"
            neighbors.append((dir_label, n_id))
        return neighbors

    def count_adjacent_monsters(self, curr_room_id):
        count = 0
        for n_id in self.room_adj.get(curr_room_id, []):
            m = self.monsters.get(n_id)
            if m and m.state != 'dead':
                count += 1
        return count

    def draw(self, surf, player):
        self.portal_anim += 0.05

        # 1. Gambar Seluruh Ruangan (Lantai Menyatu Mulus / Fog Gelap)
        for rid, info in self.rooms_info.items():
            is_visible = info['explored'] or info['is_goal']

            for rect in info['rects']:
                if is_visible:
                    floor_col = (45, 50, 68) if info['is_goal'] else COLOR_FLOOR
                    pygame.draw.rect(surf, floor_col, rect)
                    # Ubin lantai bersambung seragam
                    start_x = rect.left - (rect.left % TILE_SIZE)
                    for x in range(start_x, rect.right, TILE_SIZE):
                        if x >= rect.left:
                            pygame.draw.line(surf, COLOR_FLOOR_TILE_LINE, (x, rect.top), (x, rect.bottom))
                    start_y = rect.top - (rect.top % TILE_SIZE)
                    for y in range(start_y, rect.bottom, TILE_SIZE):
                        if y >= rect.top:
                            pygame.draw.line(surf, COLOR_FLOOR_TILE_LINE, (rect.left, y), (rect.right, y))
                else:
                    pygame.draw.rect(surf, (0, 0, 0), rect)

        # 2. Portal Finish (Selalu Nampak Bercahaya)
        pulse = abs(math.sin(self.portal_anim)) * 5.0
        pad_r = self.portal_rect.inflate(int(pulse), int(pulse))
        pygame.draw.rect(surf, COLOR_PORTAL_PAD, pad_r, border_radius=8)
        pygame.draw.rect(surf, COLOR_PORTAL_GLOW, pad_r, 2, border_radius=8)
        pygame.draw.circle(surf, (140, 240, 255), self.portal_rect.center, int(10 + pulse * 0.4))
        render_text(surf, "★ FINISH PORTAL ★", (self.portal_rect.centerx, self.portal_rect.top - 10), 10, (140, 240, 255), bold=True, center=True)

        # 3. Balok Pelindung Hijau Hunter Assassin
        for rid, b_list in self.room_containers.items():
            if self.rooms_info[rid]['explored'] or self.rooms_info[rid]['is_goal']:
                for b in b_list:
                    bx, by, bw, bh = b
                    pygame.draw.rect(surf, COLOR_CONTAINER, (bx, by, bw, bh), border_radius=3)
                    pygame.draw.rect(surf, COLOR_CONTAINER_HIGHLIGHT, (bx + 1, by + 1, bw - 2, 4), border_radius=2)
                    pygame.draw.rect(surf, COLOR_CONTAINER_DARK, (bx + 1, by + bh - 5, bw - 2, 4), border_radius=2)
                    pygame.draw.rect(surf, COLOR_CONTAINER_BORDER, (bx, by, bw, bh), 1, border_radius=3)

        # 4. Gambar Monster
        for rid, m in self.monsters.items():
            if m and m.state != 'dead' and self.rooms_info[rid]['explored']:
                m.draw(surf)

        # 5. Dinding Batu Pembatas Antar-Ruangan
        for w in self.walls:
            wx, wy, ww, wh = w
            pygame.draw.rect(surf, COLOR_WALL, (wx, wy, ww, wh))
            pygame.draw.rect(surf, COLOR_WALL_HIGHLIGHT, (wx, wy, ww, 2))
            pygame.draw.rect(surf, COLOR_WALL_SHADOW, (wx, wy + wh - 2, ww, 2))
            pygame.draw.rect(surf, COLOR_WALL_BORDER, (wx, wy, ww, wh), 1)

        # 6. Gambar Ninja (dengan efek Vanish jika skill2 aktif)
        if player.skill2_active:
            # Ninja setengah transparan berwarna cyan saat Vanish
            vanish_alpha = int(60 + abs(math.sin(pygame.time.get_ticks() * 0.008)) * 55)
            # Efek aura hologram Vanish
            vx, vy = int(player.pos.x), int(player.pos.y)
            aura_v = pygame.Surface((player.radius * 3, player.radius * 3), pygame.SRCALPHA)
            pulse_v = abs(math.sin(pygame.time.get_ticks() * 0.009)) * 4
            pygame.draw.circle(aura_v, (40, 220, 255, 50),
                               (player.radius + 6, player.radius + 6),
                               int(player.radius + 4 + pulse_v), 2)
            surf.blit(aura_v, (vx - player.radius - 6, vy - player.radius - 6))
            player.draw(surf, alpha_override=vanish_alpha)
        elif player.skill1_active:
            # Efek afterburn emas saat Dash Strike
            player.draw(surf)
            dash_surf = pygame.Surface((player.radius * 3, player.radius * 3), pygame.SRCALPHA)
            pulse_d = abs(math.sin(pygame.time.get_ticks() * 0.02)) * 5
            pygame.draw.circle(dash_surf, (255, 180, 0, 100),
                               (player.radius + 6, player.radius + 6),
                               int(player.radius + 3 + pulse_d), 3)
            surf.blit(dash_surf, (int(player.pos.x) - player.radius - 6,
                                  int(player.pos.y) - player.radius - 6))
        else:
            player.draw(surf)


# ============================================================
#  KELAS: Game (Pengendali Utama & Efek Screen Shake)
# ============================================================

class Game:
    """Manajer Game dengan mode Normal & Hard, efek tebasan sabit, dan pertarungan stealth."""

    def __init__(self):
        pygame.init()
        pygame.mixer.init(
            frequency=AUDIO_CONFIG['sample_rate'],
            size=AUDIO_CONFIG['bit_depth'],
            channels=AUDIO_CONFIG['channels'],
            buffer=AUDIO_CONFIG['buffer_size']
        )
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"{GAME_TEXTS['title']} - {GAME_TEXTS['subtitle']}")
        self.clock = pygame.time.Clock()

        self.synth = SoundSynthesizer()
        self.sounds = {
            'slash': pygame.mixer.Sound(self.synth.generate_slash_sound(0.4)),
            'claw': pygame.mixer.Sound(self.synth.generate_claw_sound(0.35)),
            'alert': pygame.mixer.Sound(self.synth.generate_alert_sound(0.35)),
            'portal': pygame.mixer.Sound(self.synth.generate_door_sound(0.35)),
            'victory': pygame.mixer.Sound(self.synth.generate_victory_sound(0.45)),
            'gameover': pygame.mixer.Sound(self.synth.generate_gameover_sound(0.4)),
        }

        self.analyzer = BayesianThreatAnalyzer()
        self.advisor = ExpectedUtilityAdvisor()
        self.entropy_calc = ShannonEntropyCalculator()

        self.difficulty = 'NORMAL'
        self.state = 'PLAY'
        self.map = MultiShapeRoomGridMap(difficulty=self.difficulty)

        start_x, start_y = self.map.get_safe_spawn_point(self.map.start_room_id, radius=NINJA_CONFIG['radius'])
        speed_mult = DIFFICULTY_CONFIG[self.difficulty]['ninja_speed_mult']
        self.player = Player(start_x, start_y, speed_mult=speed_mult)

        # Partikel & Efek Visual
        self.damage_texts = []
        self.claw_marks = []
        self.slash_arcs = []
        self.sparks = []
        self.confetti = []

        # Screen Shake FX
        self.shake_time = 0.0
        self.shake_intensity = 0.0

        self.victory_timer = 0.0
        self.victory_bounce = 0.0

        self.current_room = self.map.start_room_id
        self.bayesian_analysis = {}

        self._update_perception_and_clues()

    def trigger_screen_shake(self, intensity=3.5, duration=0.14):
        """Memicu getaran layar saat serangan terjadi."""
        self.shake_intensity = intensity
        self.shake_time = duration

    def _activate_dash_strike(self):
        """
        SKILL 1 — DASH STRIKE:
        Ninja menerjang ke arah hadap (DENGAN PEMERIKSAAN TEMBOK KETAT / SUB-STEPPING).
        Tidak dapat menembus tembok, tidak dapat melompat keluar ruangan terkunci.
        Monster di depan sepanjang pedang di ruangan yang sama & tidak terhalang tembok terkena damage & mati.
        """
        facing = self.player.facing
        dash_dist = self.player.skill1_range  # 70 px
        pr = self.player.radius
        curr_room = self.current_room

        # SUB-STEPPING KETAT: Gerak per 1.5 pixel agar TIDAK PERNAH MENEMBUS TEMBOK
        step_dist = 1.5
        num_steps = max(1, int(dash_dist / step_dist))
        dx_step = math.cos(facing) * step_dist
        dy_step = math.sin(facing) * step_dist

        curr_x, curr_y = self.player.pos.x, self.player.pos.y

        for _ in range(num_steps):
            next_x = curr_x + dx_step
            next_y = curr_y + dy_step

            # 1. Cek tabrakan dengan semua dinding map
            hit_wall = False
            for w in self.map.collision_rects:
                if circle_rect_collision(next_x, next_y, pr, w[0], w[1], w[2], w[3]):
                    hit_wall = True
                    break
            if hit_wall:
                break

            # 2. Cek tabrakan dengan balok kontainer tengah
            for rid_b, blist in self.map.room_containers.items():
                for bx, by, bw, bh in blist:
                    if circle_rect_collision(next_x, next_y, pr, bx, by, bw, bh):
                        hit_wall = True
                        break
                if hit_wall:
                    break
            if hit_wall:
                break

            # 3. Kunci Ruangan: Jika ruangan ada monster, tidak boleh dash menyeberang keluar ruangan
            curr_monster = self.map.monsters.get(curr_room)
            if curr_monster and curr_monster.state != 'dead':
                if self.map.get_room_id_at(next_x, next_y) != curr_room:
                    break

            # 4. Batas Grid Dungeon
            if not (self.map.margin_x + pr <= next_x <= self.map.margin_x + self.map.grid_w - pr and
                    self.map.margin_y + pr <= next_y <= self.map.margin_y + self.map.grid_h - pr):
                break

            curr_x, curr_y = next_x, next_y

        self.player.pos.update(curr_x, curr_y)
        self.trigger_screen_shake(intensity=6.0, duration=0.22)

        # Tebasan beruntun: monster di depan sepanjang pedang di ruangan yang sama
        # DAN tidak terhalang tembok (Line-of-Sight) -> MATI
        hit_any = False
        sword_range = self.player.skill1_range
        for rid, monster in self.map.monsters.items():
            if monster and monster.state != 'dead' and rid == self.current_room:
                dist_m = distance(
                    (self.player.pos.x, self.player.pos.y),
                    (monster.pos.x, monster.pos.y)
                )
                if dist_m <= sword_range + monster.radius:
                    angle_to_mon = math.atan2(
                        monster.pos.y - self.player.pos.y,
                        monster.pos.x - self.player.pos.x
                    )
                    diff = abs(normalize_angle(angle_to_mon - facing))
                    if diff <= math.radians(90):
                        # Cek apakah terhalang tembok
                        p1 = (self.player.pos.x, self.player.pos.y)
                        p2 = (monster.pos.x, monster.pos.y)
                        wall_blocked = any(line_blocked_by_rect(p1, p2, w[0], w[1], w[2], w[3]) for w in self.map.collision_rects)
                        if not wall_blocked:
                            monster.state = 'dead'
                            reward = monster.stats['gold_reward']
                            self.player.gold += reward
                            self.player.kill_count += 1

                            slash_angle = angle_to_mon
                            for _ in range(3):
                                self.slash_arcs.append(SlashArcFX(monster.pos.x, monster.pos.y, slash_angle + random.uniform(-0.4, 0.4)))
                            for _ in range(28):
                                self.sparks.append(SparkParticle(monster.pos.x, monster.pos.y, slash_angle))
                            hit_any = True

        if hit_any:
            self.sounds['slash'].play()
            self._update_perception_and_clues()

        # Partikel pendorong dash
        for _ in range(16):
            angle_back = facing + math.pi + random.uniform(-0.5, 0.5)
            self.sparks.append(SparkParticle(
                self.player.pos.x + math.cos(angle_back) * 8,
                self.player.pos.y + math.sin(angle_back) * 8,
                angle_back
            ))

    def _handle_attack_input(self):
        """
        Menangani tombol SPASI untuk menyerang:
        - Bentuk serangan adalah DASH MENYERGAP (Dash Strike).
        - Serangan HANYA BISA DILAKUKAN & MUNCUL jika ada musuh di samping/belakang kita (atau saat Vanish).
        - Jika tidak ada musuh di samping, tidak dapat menyerang dan tidak muncul serangan.
        - Teks damage melayang dihapus agar layar bersih dan tidak mengganggu.
        """
        curr_monster = self.map.monsters.get(self.current_room)
        if not curr_monster or curr_monster.state == 'dead':
            return

        dist_m = distance((self.player.pos.x, self.player.pos.y), (curr_monster.pos.x, curr_monster.pos.y))

        # Cek apakah terhalang tembok antara pemain dan monster
        p1 = (self.player.pos.x, self.player.pos.y)
        p2 = (curr_monster.pos.x, curr_monster.pos.y)
        wall_blocked = any(line_blocked_by_rect(p1, p2, w[0], w[1], w[2], w[3]) for w in self.map.collision_rects)
        if wall_blocked:
            return

        # Cek sudut hadap monster: apakah pemain berada di samping atau belakang monster?
        dx = self.player.pos.x - curr_monster.pos.x
        dy = self.player.pos.y - curr_monster.pos.y
        angle_to_player = math.atan2(dy, dx)
        diff_from_facing = abs(normalize_angle(angle_to_player - curr_monster.facing))
        is_beside_or_behind = (diff_from_facing >= math.radians(60))

        can_attack = False

        # Kondisi 1: Skill 2 (Vanish) aktif -> jangkauan meningkat (85px), bisa menyergap dari bayangan
        if self.player.skill2_active:
            if dist_m <= 85.0:
                can_attack = True

        # Kondisi 2: Normal (tanpa Vanish) -> musuh harus berada di samping/belakang saat patroli (jangkauan ~58px)
        else:
            if dist_m <= 58.0 and is_beside_or_behind and curr_monster.state == 'patrol':
                can_attack = True

        # Jika syarat tidak terpenuhi (tidak ada musuh di samping), tidak menyerang & tidak muncul serangan!
        if not can_attack:
            return

        # ── EKSEKUSI SERANGAN BENTUK DASH MENYERGAP KE ARAH MONSTER ──
        angle_to_mon = math.atan2(curr_monster.pos.y - self.player.pos.y, curr_monster.pos.x - self.player.pos.x)
        self.player.facing = angle_to_mon
        self.player.target_facing = angle_to_mon

        # Jarak dash: mendekat langsung hingga batas lingkar monster (sub-stepping tanpa tembus tembok)
        target_dist = max(0.0, dist_m - (self.player.radius + curr_monster.radius + 3))
        step_size = 2.0
        num_steps = int(target_dist / step_size)
        dx_step = math.cos(angle_to_mon) * step_size
        dy_step = math.sin(angle_to_mon) * step_size

        cur_x, cur_y = self.player.pos.x, self.player.pos.y
        for _ in range(num_steps):
            nxt_x, nxt_y = cur_x + dx_step, cur_y + dy_step
            if any(circle_rect_collision(nxt_x, nxt_y, self.player.radius, w[0], w[1], w[2], w[3]) for w in self.map.collision_rects):
                break
            cur_x, cur_y = nxt_x, nxt_y

        # Jejak bayangan siluet dash (phantom after-images)
        self.player.trail.append((vec2(self.player.pos.x, self.player.pos.y), self.player.facing, 1.0))
        self.player.trail.append((vec2((self.player.pos.x + cur_x) * 0.5, (self.player.pos.y + cur_y) * 0.5), self.player.facing, 1.0))
        self.player.pos.update(cur_x, cur_y)
        self.player.trail.append((vec2(self.player.pos.x, self.player.pos.y), self.player.facing, 1.0))

        # Efek visual tebasan pedang sabit & suara tebasan
        self.player.slash_anim_timer = 0.18
        self.sounds['slash'].play()

        slash_angle = angle_to_mon
        self.slash_arcs.append(SlashArcFX(curr_monster.pos.x, curr_monster.pos.y, slash_angle))
        for _ in range(16):
            self.sparks.append(SparkParticle(curr_monster.pos.x, curr_monster.pos.y, slash_angle))
        self.trigger_screen_shake(intensity=4.0, duration=0.15)

        # Jika Skill 2 (Vanish) aktif, batalkan dan mulai cooldown 9 detik
        if self.player.skill2_active:
            self.player.cancel_vanish()

        # Kurangi hit monster (tanpa teks floating damage)
        curr_monster.hits_remaining -= 1
        curr_monster.hit_invulnerable_timer = 0.40

        push_dir = vec2(math.cos(angle_to_player), math.sin(angle_to_player)) * -8
        curr_monster.pos += push_dir

        if curr_monster.hits_remaining > 0:
            # Monster kaget & langsung berbalik mengejar
            curr_monster.state = 'chase'
            curr_monster.was_chasing = True
            curr_monster.target_facing = math.atan2(self.player.pos.y - curr_monster.pos.y, self.player.pos.x - curr_monster.pos.x)
            curr_monster.facing = curr_monster.target_facing
            if 'alert' in self.sounds:
                self.sounds['alert'].play()
        else:
            curr_monster.state = 'dead'
            reward = curr_monster.stats['gold_reward']
            self.player.gold += reward
            self.player.kill_count += 1
            for _ in range(20):
                self.sparks.append(SparkParticle(curr_monster.pos.x, curr_monster.pos.y))
            self._update_perception_and_clues()

    def toggle_difficulty(self):
        """Beralih mode: di Hard mode damage lebih sakit & ruangan jalan lebih sedikit."""
        self.difficulty = 'HARD' if self.difficulty == 'NORMAL' else 'NORMAL'
        diff_cfg = DIFFICULTY_CONFIG[self.difficulty]
        self.map.difficulty = self.difficulty
        self.map.reseed_monsters()  # Tata ulang monster sesuai prior mode baru
        self.player.apply_difficulty(diff_cfg['ninja_speed_mult'])
        self._update_perception_and_clues()

    def _update_perception_and_clues(self):
        self.player.adjacent_monsters_count = self.map.count_adjacent_monsters(self.current_room)
        neighbors = self.map.get_adjacent_rooms(self.current_room)
        analysis = {}
        is_hard = (self.difficulty == 'HARD')

        for dir_name, n_id in neighbors:
            r_info = self.map.rooms_info[n_id]
            depth = r_info['depth']
            clue = r_info['clue']
            explored = r_info['explored']

            posterior = self.analyzer.compute_posterior(depth, clue, is_hard=is_hard)
            eu_val = self.advisor.compute_expected_utility(posterior)
            entropy = self.entropy_calc.compute_entropy(posterior)

            analysis[n_id] = {
                'dir': dir_name,
                'depth': depth,
                'clue': clue,
                'explored': explored,
                'posterior': posterior,
                'eu': eu_val,
                'entropy': entropy,
                'is_goal': r_info['is_goal'],
            }

        unexplored_candidates = {nid: data for nid, data in analysis.items() if not data['explored']}
        if unexplored_candidates:
            best_id = max(unexplored_candidates, key=lambda nid: unexplored_candidates[nid]['eu'])
        else:
            best_id = max(analysis, key=lambda nid: analysis[nid]['eu']) if analysis else None

        self.bayesian_analysis = {
            'neighbors': analysis,
            'best_id': best_id,
        }

    def restart_game(self):
        self.map = MultiShapeRoomGridMap(difficulty=self.difficulty)
        start_x, start_y = self.map.get_safe_spawn_point(self.map.start_room_id, radius=NINJA_CONFIG['radius'])
        speed_mult = DIFFICULTY_CONFIG[self.difficulty]['ninja_speed_mult']
        self.player = Player(start_x, start_y, speed_mult=speed_mult)

        self.damage_texts.clear()
        self.claw_marks.clear()
        self.slash_arcs.clear()
        self.sparks.clear()
        self.confetti.clear()
        self.victory_timer = 0.0
        self.current_room = self.map.start_room_id
        self.state = 'PLAY'
        self._update_perception_and_clues()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self.toggle_difficulty()

                # ── SKILL 1: DASH STRIKE (Tekan 1) — Cooldown 2,3 detik ──
                if event.key == pygame.K_1 and self.state == 'PLAY':
                    if not self.player.skill1_active and self.player.skill1_cd_timer <= 0:
                        self.player.skill1_active = True
                        self.player.skill1_timer  = self.player.skill1_duration
                        self.player.skill1_cd_timer = self.player.skill1_cooldown  # Cooldown 2,3 detik aktif
                        self._activate_dash_strike()

                # ── SKILL 2: VANISH (Tekan 2) ──
                if event.key == pygame.K_2 and self.state == 'PLAY':
                    if not self.player.skill2_active and self.player.skill2_cd_timer <= 0:
                        self.player.skill2_active = True
                        self.player.skill2_timer = self.player.skill2_duration

                # ── TOMBOL SPASI: SERANG (Jarak serangan meningkat saat Skill 2 Vanish aktif) ──
                if event.key == pygame.K_SPACE and self.state == 'PLAY':
                    self._handle_attack_input()

                if self.state in ('VICTORY', 'GAMEOVER'):
                    if event.key == pygame.K_r:
                        self.restart_game()

    def update(self, dt):
        keys = pygame.key.get_pressed()

        # Update Screen Shake
        if self.shake_time > 0:
            self.shake_time -= dt
            if self.shake_time <= 0:
                self.shake_intensity = 0.0

        # Update skill timer player
        self.player.update_skills(dt)

        # Update Efek Melayang & Partikel
        for dt_obj in list(self.damage_texts):
            dt_obj.update()
            if dt_obj.life <= 0:
                self.damage_texts.remove(dt_obj)

        for cm_obj in list(self.claw_marks):
            cm_obj.update()
            if cm_obj.life <= 0:
                self.claw_marks.remove(cm_obj)

        for sa in list(self.slash_arcs):
            sa.update()
            if sa.life <= 0:
                self.slash_arcs.remove(sa)

        for spk in list(self.sparks):
            spk.update()
            if spk.life <= 0:
                self.sparks.remove(spk)

        # ----------------------------------------------------
        # STATE: BERMAIN (PLAY)
        # ----------------------------------------------------
        if self.state == 'PLAY':
            move_vec = self.player.handle_input(keys)
            old_x, old_y = self.player.pos.x, self.player.pos.y
            self.player.update(move_vec, self.map.collision_rects)

            # Push-out player dari box pelindung jika overlap
            # (box tidak ada di collision_rects agar bisa dikelilingi, tapi tetap padat)
            pr = self.player.radius
            px, py = self.player.pos.x, self.player.pos.y
            for rid_b, blist in self.map.room_containers.items():
                for bx, by, bw, bh in blist:
                    # Hitung overlap lingkaran-rect dan dorong keluar
                    nearest_x = max(bx, min(px, bx + bw))
                    nearest_y = max(by, min(py, by + bh))
                    dist_x = px - nearest_x
                    dist_y = py - nearest_y
                    dist2 = dist_x * dist_x + dist_y * dist_y
                    if dist2 < pr * pr and dist2 > 0.0001:
                        dist = math.sqrt(dist2)
                        # Dorong keluar dengan jarak minimal
                        overlap = pr - dist
                        self.player.pos.x += (dist_x / dist) * overlap
                        self.player.pos.y += (dist_y / dist) * overlap
                        px, py = self.player.pos.x, self.player.pos.y

            # Cek di Ruangan mana Ninja berada
            new_room_id = self.map.get_room_id_at(self.player.pos.x, self.player.pos.y)
            if new_room_id != self.current_room:
                curr_monster = self.map.monsters.get(self.current_room)
                if curr_monster and curr_monster.state != 'dead':
                    # KUNCI RUANGAN: Kembalikan posisi ninja ke dalam ruangan saat ini
                    self.player.pos.update(old_x, old_y)
                else:
                    self.current_room = new_room_id
                    self.map.rooms_info[self.current_room]['explored'] = True
                    self._update_perception_and_clues()

            # Cek status bahaya: apakah ada monster di ruangan ini yang sedang mengejar/menyerang kita
            curr_monster = self.map.monsters.get(self.current_room)
            self.player.being_attacked = bool(curr_monster and curr_monster.state == 'chase' and curr_monster.state != 'dead')

            # Ninja Vanish → monster tidak bisa mendeteksi (patroli paksa)
            is_ninja_invisible = self.player.skill2_active

            # Update Monster & Combat
            for rid, monster in self.map.monsters.items():
                if monster and monster.state != 'dead':
                    is_player_in_same_room = (rid == self.current_room)
                    # Jika ninja Vanish → sembunyikan dari monster (treat as not in room)
                    effective_in_room = is_player_in_same_room and not is_ninja_invisible
                    monster.update(self.player, dt, self.sounds, self.damage_texts, self.claw_marks, effective_in_room)

                    if is_player_in_same_room and not is_ninja_invisible:
                        dist_m = distance((self.player.pos.x, self.player.pos.y), (monster.pos.x, monster.pos.y))
                        if dist_m <= (self.player.radius + monster.radius + 6):
                            # Jika monster sedang mengejar kita (chase), monster mencakar ninja saat kontak fisik
                            # (Pemain TIDAK menyerang otomatis lagi; pemain harus menekan tombol SPASI untuk menyerang!)
                            if monster.state == 'chase':
                                if monster.cooldown_timer <= 0:
                                    self.player.hp -= monster.damage
                                    monster.cooldown_timer = monster.attack_cooldown
                                    self.sounds['claw'].play()
                                    self.trigger_screen_shake(intensity=4.5, duration=0.18)
                                    self.claw_marks.append(ClawMark(self.player.pos.x, self.player.pos.y))

            if self.player.hp <= 0:
                self.player.hp = 0
                self.state = 'GAMEOVER'
                self.sounds['gameover'].play()
                return

            # Cek Kemenangan
            if self.current_room == self.map.goal_room_id:
                if self.map.portal_rect.collidepoint(int(self.player.pos.x), int(self.player.pos.y)):
                    self.state = 'VICTORY'
                    self.sounds['victory'].play()
                    self.confetti = [
                        ConfettiParticle(random.uniform(50, SCREEN_WIDTH - 50), random.uniform(-100, 250))
                        for _ in range(CAMERA_CONFIG['confetti_count'])
                    ]

        elif self.state == 'VICTORY':
            self.victory_timer += dt
            self.victory_bounce = abs(math.sin(self.victory_timer * 6.0)) * 26.0

            if len(self.confetti) < 180 and random.random() < 0.2:
                self.confetti.append(ConfettiParticle(random.uniform(50, SCREEN_WIDTH - 50), -20))

            for p in list(self.confetti):
                p.update()
                if p.life <= 0 or p.pos.y > SCREEN_HEIGHT + 20:
                    self.confetti.remove(p)

    def draw_bayesian_panel(self, surf):
        panel_x = GAME_AREA_WIDTH
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT)

        pygame.draw.rect(surf, COLOR_PANEL_BG, panel_rect)
        pygame.draw.line(surf, COLOR_PANEL_BORDER, (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

        render_text(surf, "[ PERSEPSI MINESWEEPER ]", (panel_x + PANEL_WIDTH // 2, 16), 15, COLOR_PANEL_TITLE, bold=True, center=True)
        r_type = self.map.rooms_info[self.current_room]['type'].upper()
        depth_cur = self.map.rooms_info[self.current_room]['depth']
        render_text(surf, f"Ruang #{self.current_room} ({r_type}) | Lantai: {depth_cur}/5", (panel_x + PANEL_WIDTH // 2, 36), 11, (170, 170, 190), center=True)

        # Kartu Kesulitan
        diff_info = DIFFICULTY_CONFIG[self.difficulty]
        diff_box = pygame.Rect(panel_x + 14, 52, PANEL_WIDTH - 28, 26)
        pygame.draw.rect(surf, (25, 20, 30), diff_box, border_radius=4)
        pygame.draw.rect(surf, diff_info['color'], diff_box, 1, border_radius=4)
        render_text(surf, f"MODE: {diff_info['name_id']}  [Tekan H]", (panel_x + PANEL_WIDTH // 2, 65), 11, diff_info['color'], bold=True, center=True)

        cnt = self.player.adjacent_monsters_count
        stat_color = (80, 240, 120) if cnt == 0 else ((255, 200, 50) if cnt == 1 else (255, 80, 80))
        render_text(surf, f"Monster di Bilik Sekitar : {cnt} Monster", (panel_x + 16, 84), 12, stat_color, bold=True)

        pygame.draw.line(surf, (40, 40, 60), (panel_x + 12, 102), (panel_x + PANEL_WIDTH - 12, 102), 1)

        neighbors = self.bayesian_analysis.get('neighbors', {})
        best_id = self.bayesian_analysis.get('best_id')

        y_cursor = 108
        render_text(surf, "ANALISIS RUANGAN SEKITAR:", (panel_x + 16, y_cursor), 11, COLOR_PANEL_HIGHLIGHT, bold=True)
        y_cursor += 18

        displayed_items = list(neighbors.items())[:4]

        for n_id, data in displayed_items:
            is_best = (n_id == best_id)
            is_explored = data['explored']
            is_goal = data['is_goal']

            card_col = (35, 45, 65) if is_best else (24, 24, 34)
            card_border = (80, 220, 120) if is_best else ((80, 200, 255) if is_goal else (45, 45, 60))

            card_h = 120
            card_rect = pygame.Rect(panel_x + 10, y_cursor, PANEL_WIDTH - 20, card_h)
            pygame.draw.rect(surf, card_col, card_rect, border_radius=6)
            pygame.draw.rect(surf, card_border, card_rect, 2 if is_best else 1, border_radius=6)

            dir_title = f"{data['dir']} (Ruang #{n_id})"
            render_text(surf, dir_title, (panel_x + 16, y_cursor + 4), 11, (240, 230, 200), bold=True)

            if is_goal:
                render_text(surf, "[FINISH]", (panel_x + 135, y_cursor + 4), 10, (100, 240, 255), bold=True)
            else:
                status_str = "TERBUKA" if is_explored else "GELAP"
                status_col = (80, 255, 120) if is_explored else (220, 100, 100)
                render_text(surf, f"[{status_str}]", (panel_x + 135, y_cursor + 4), 10, status_col, bold=True)

            eu_val = data['eu']
            risk_label, risk_col = self.advisor.get_risk_level(eu_val)
            render_text(surf, f"EU: {eu_val:+.1f}", (panel_x + PANEL_WIDTH - 65, y_cursor + 4), 11, risk_col, bold=True)

            bar_y = y_cursor + 22
            for threat in THREAT_TYPES:
                prob = data['posterior'].get(threat, 0.0)
                if threat == 'safe':
                    b_col = (60, 200, 80)
                elif threat in ('goblin_scout', 'orc_sentry'):
                    b_col = (240, 180, 40)
                else:
                    b_col = (240, 60, 60)

                t_abbr = THREAT_NAMES_ID[threat].split()[0]
                render_text(surf, f"{t_abbr[:5]}:", (panel_x + 16, bar_y), 9, (150, 150, 170))

                bar_max_w = 115
                actual_w = int(bar_max_w * prob)
                pygame.draw.rect(surf, (30, 30, 45), (panel_x + 65, bar_y + 3, bar_max_w, 6), border_radius=2)
                if actual_w > 0:
                    pygame.draw.rect(surf, b_col, (panel_x + 65, bar_y + 3, actual_w, 6), border_radius=2)

                render_text(surf, f"{prob*100:4.1f}%", (panel_x + 188, bar_y - 2), 9, (210, 210, 230))
                bar_y += 15

            if is_best:
                render_text(surf, "★ REKOMENDASI MEU ★", (panel_x + PANEL_WIDTH // 2, y_cursor + 104), 9, (80, 255, 120), bold=True, center=True)

            y_cursor += card_h + 5

        box_ctrl = pygame.Rect(panel_x + 10, SCREEN_HEIGHT - 98, PANEL_WIDTH - 20, 88)
        pygame.draw.rect(surf, (20, 20, 30), box_ctrl, border_radius=6)
        pygame.draw.rect(surf, (50, 50, 70), box_ctrl, 1, border_radius=6)
        render_text(surf, "[ MEKANIK HUNTER ASSASSIN ]", (panel_x + PANEL_WIDTH // 2, SCREEN_HEIGHT - 91), 11, COLOR_PANEL_TITLE, bold=True, center=True)
        render_text(surf, "Diserang -> Marah: Monster langsung kejar & KEBAL!", (panel_x + 16, SCREEN_HEIGHT - 73), 10, (255, 60, 60))
        render_text(surf, "Wajib Sembunyi : Berlindung di balok sebelum hit lagi", (panel_x + 16, SCREEN_HEIGHT - 56), 10, (100, 255, 150))
        render_text(surf, "Serang Manual   : Tekan [SPASI] (samping/belakang)", (panel_x + 16, SCREEN_HEIGHT - 39), 10, (255, 220, 100))
        render_text(surf, "Jalur Berkelok : Ikuti Rekomendasi Bayes MEU!", (panel_x + 16, SCREEN_HEIGHT - 22), 9, (140, 220, 255))

    def draw_hud(self, surf):
        hud_surf = pygame.Surface((GAME_AREA_WIDTH, 36), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (15, 15, 25, 220), (0, 0, GAME_AREA_WIDTH, 36))
        pygame.draw.line(hud_surf, (50, 50, 70), (0, 35), (GAME_AREA_WIDTH, 35), 1)

        hp_pct = max(0.0, min(1.0, self.player.hp / self.player.max_hp))
        bar_w = 140
        bar_h = 13
        bx, by = 16, 11
        pygame.draw.rect(hud_surf, COLOR_HP_BG, (bx, by, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(hud_surf, COLOR_HP_BAR, (bx, by, int(bar_w * hp_pct), bar_h), border_radius=3)
        pygame.draw.rect(hud_surf, COLOR_HP_BORDER, (bx, by, bar_w, bar_h), 1, border_radius=3)
        render_text(hud_surf, f"HP: {int(self.player.hp)} / {self.player.max_hp}", (bx + 8, by - 2), 10, (255, 255, 255), bold=True)

        render_text(hud_surf, f"GOLD: {self.player.gold}", (185, 9), 12, COLOR_GOLD_ICON, bold=True)
        render_text(hud_surf, f"KILLS: {self.player.kill_count}", (280, 9), 12, (255, 110, 110), bold=True)

        diff_col = DIFFICULTY_CONFIG[self.difficulty]['color']
        render_text(hud_surf, f"[{self.difficulty}]", (370, 9), 12, diff_col, bold=True)

        explored_count = sum(1 for info in self.map.rooms_info.values() if info['explored'])
        render_text(hud_surf, f"RUANGAN: {explored_count} / {self.map.total_rooms}", (GAME_AREA_WIDTH - 150, 9), 12, (100, 200, 255), bold=True)

        surf.blit(hud_surf, (0, 0))

        current_monster = self.map.monsters.get(self.current_room)
        if current_monster and current_monster.state != 'dead':
            ticks = pygame.time.get_ticks()
            if (ticks // 500) % 2 == 0:
                lock_font = pygame.font.SysFont('segoe ui', 13, bold=True)
                lock_surf = lock_font.render("RUANGAN TERKUNCI — Kalahkan Monster untuk Keluar!", True, (255, 60, 60))
                lock_rect = lock_surf.get_rect(center=(GAME_AREA_WIDTH // 2, SCREEN_HEIGHT - 20))
                bg_rect = lock_rect.inflate(16, 6)
                bg_s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(bg_s, (30, 0, 0, 200), bg_s.get_rect(), border_radius=5)
                surf.blit(bg_s, bg_rect.topleft)
                surf.blit(lock_surf, lock_rect)

    def _draw_skill_graphic(self, surf, skill_idx, cx, cy, is_active, is_ready):
        """
        Menggambar ilustrasi ikon visual (gambar vektor khas game laga):
        - Skill 0 (DASH): Pedang katana menerjang dengan jejak kecepatan & tebasan sabit.
        - Skill 1 (VANISH): Topeng ninja misterius yang larut dalam asap/kabut bayangan.
        """
        if skill_idx == 0:
            # ──────────────────────────────────────────────────────────
            # GAMBAR SKILL 1: DASH STRIKE (Pedang Katana & Kilatan Sabit)
            # ──────────────────────────────────────────────────────────
            trail_col = (230, 140, 255) if is_ready else (75, 65, 95)
            blade_col = (255, 255, 255) if is_ready else (140, 140, 160)
            hilt_col  = (200, 40, 40) if is_ready else (85, 45, 50)
            guard_col = (255, 215, 60) if is_ready else (100, 90, 60)
            arc_col   = (255, 235, 110) if is_ready else (80, 80, 100)

            # 1. Tiga garis jejak kecepatan horizontal di belakang (Speed Trails)
            pygame.draw.line(surf, trail_col, (cx - 15, cy - 6), (cx - 5, cy - 6), 2)
            pygame.draw.line(surf, trail_col, (cx - 13, cy + 1), (cx - 1, cy + 1), 2)
            pygame.draw.line(surf, trail_col, (cx - 16, cy + 8), (cx - 7, cy + 8), 1)

            # 2. Gagang Pedang Scabbard (Tsuka Merah Terbungkus)
            pygame.draw.line(surf, hilt_col, (cx - 11, cy + 11), (cx - 5, cy + 5), 3)

            # 3. Penjaga Pedang Emas (Tsuba)
            pygame.draw.line(surf, guard_col, (cx - 8, cy + 3), (cx - 3, cy + 8), 3)

            # 4. Bilah Katana Baja Mengkilap Tajam
            b_start = (cx - 4, cy + 4)
            b_end   = (cx + 12, cy - 12)
            pygame.draw.line(surf, (180, 195, 230), b_start, b_end, 3)
            pygame.draw.line(surf, blade_col, (b_start[0], b_start[1] - 1), (b_end[0], b_end[1] - 1), 1)

            # 5. Busur Kilatan Sabit Tebasan di Ujung Pedang
            arc_rect = pygame.Rect(cx - 3, cy - 17, 20, 20)
            pygame.draw.arc(surf, arc_col, arc_rect, 0.2, 1.8, 2)

            # 6. Percikan Petir Kuning di Ujung Pedang
            if is_ready:
                spark_pts = [(cx + 10, cy - 13), (cx + 14, cy - 15), (cx + 11, cy - 9)]
                pygame.draw.lines(surf, (255, 255, 180), False, spark_pts, 2)

        elif skill_idx == 1:
            # ──────────────────────────────────────────────────────────
            # GAMBAR SKILL 2: VANISH (Topeng Ninja Melarut dalam Asap)
            # ──────────────────────────────────────────────────────────
            hood_col  = (38, 58, 82) if is_ready else (35, 42, 52)
            mask_col  = (22, 36, 52) if is_ready else (25, 30, 40)
            eye_col   = (60, 240, 255) if is_ready else (70, 110, 130)
            smoke_col = (70, 190, 230) if is_ready else (50, 70, 90)

            # 1. Tudung Kepala Ninja (Hood)
            pygame.draw.circle(surf, hood_col, (cx, cy - 1), 12)

            # 2. Masker Mulut Ninja
            pygame.draw.rect(surf, mask_col, (cx - 10, cy - 2, 20, 11), border_radius=3)

            # 3. Belahan Mata Gelap
            pygame.draw.ellipse(surf, (12, 18, 28), (cx - 9, cy - 6, 18, 6))

            # 4. Mata Ninja Menyala Cyan
            pygame.draw.ellipse(surf, eye_col, (cx - 7, cy - 5, 5, 3))
            pygame.draw.ellipse(surf, eye_col, (cx + 2, cy - 5, 5, 3))
            if is_ready:
                pygame.draw.circle(surf, (255, 255, 255), (cx - 5, cy - 4), 1)
                pygame.draw.circle(surf, (255, 255, 255), (cx + 4, cy - 4), 1)

            # 5. Gelembung / Pusaran Asap Menghilang (Mist & Smoke Rings)
            pygame.draw.circle(surf, smoke_col, (cx - 12, cy + 7), 4, 1)
            pygame.draw.circle(surf, smoke_col, (cx + 11, cy + 6), 5, 1)
            pygame.draw.circle(surf, smoke_col, (cx + 9, cy - 9), 3, 1)
            pygame.draw.circle(surf, smoke_col, (cx - 9, cy - 10), 2, 1)

    def draw_skills_hud(self, surf):
        """
        Gambar ikon 2 skill di pojok kiri bawah area game.
        Skill 1: Dash Strike  (cooldown 2,3 detik, [1])
        Skill 2: Vanish       (cooldown 9 detik, [2])
        """
        ticks = pygame.time.get_ticks()
        icon_size = 56
        icon_gap  = 12
        margin_x  = 14
        margin_y  = 12
        base_y    = SCREEN_HEIGHT - margin_y - icon_size

        skills = [
            {
                'key':    '1',
                'label':  'DASH',
                'icon_color': (200, 80, 255),
                'active': self.player.skill1_active,
                'ready':  (self.player.skill1_cd_timer <= 0 and not self.player.skill1_active),
                'cd':     self.player.skill1_cd_timer,
                'cd_max': self.player.skill1_cooldown,
            },
            {
                'key':    '2',
                'label':  'VANISH',
                'icon_color': (40, 200, 240),
                'active': self.player.skill2_active,
                'ready':  (self.player.skill2_cd_timer <= 0 and not self.player.skill2_active),
                'cd':     self.player.skill2_cd_timer,
                'cd_max': self.player.skill2_cooldown,
            },
        ]

        for i, sk in enumerate(skills):
            ix = margin_x + i * (icon_size + icon_gap)
            iy = base_y

            icon_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

            # 1. Latar Belakang Kartu Ikon Modern
            bg_col = (18, 16, 26, 235)
            border_col = sk['icon_color'] if sk['ready'] else (55, 55, 75)
            if sk['active']:
                pulse = (ticks // 120) % 2 == 0
                border_col = sk['icon_color'] if pulse else (255, 255, 255)

            pygame.draw.rect(icon_surf, bg_col, (0, 0, icon_size, icon_size), border_radius=10)
            pygame.draw.rect(icon_surf, border_col, (0, 0, icon_size, icon_size), 2 if (sk['ready'] or sk['active']) else 1, border_radius=10)

            # 2. Lingkaran Badge Gambar di Tengah
            circle_cx, circle_cy = icon_size // 2, 23
            circle_r = 17

            # Efek Aura Saat Aktif
            if sk['active']:
                pulse_r = int(circle_r + 3 + abs(math.sin(ticks * 0.015)) * 4)
                pygame.draw.circle(icon_surf, (*sk['icon_color'], 55), (circle_cx, circle_cy), pulse_r)

            # Latar lingkaran gambar
            badge_bg = (38, 20, 50) if (i == 0 and sk['ready']) else ((14, 30, 48) if (i == 1 and sk['ready']) else (26, 26, 36))
            pygame.draw.circle(icon_surf, badge_bg, (circle_cx, circle_cy), circle_r)
            pygame.draw.circle(icon_surf, border_col, (circle_cx, circle_cy), circle_r, 1)

            # 3. GAMBAR ILUSTRASI VISUAL SKILL
            self._draw_skill_graphic(icon_surf, i, circle_cx, circle_cy, sk['active'], sk['ready'])

            # 4. Label Nama Skill di Bawah
            lbl_font = pygame.font.SysFont('segoe ui', 9, bold=True)
            lbl_col  = sk['icon_color'] if (sk['ready'] or sk['active']) else (90, 90, 115)
            lbl_surf = lbl_font.render(sk['label'], True, lbl_col)
            lbl_r    = lbl_surf.get_rect(center=(icon_size // 2, icon_size - 9))
            icon_surf.blit(lbl_surf, lbl_r)

            # 5. Tag Tombol [1] / [2] di Pojok Kiri Atas
            tag_rect = pygame.Rect(3, 3, 14, 11)
            pygame.draw.rect(icon_surf, (30, 30, 45, 220), tag_rect, border_radius=3)
            pygame.draw.rect(icon_surf, (80, 80, 110), tag_rect, 1, border_radius=3)
            key_font = pygame.font.SysFont('segoe ui', 8, bold=True)
            key_surf = key_font.render(sk['key'], True, (240, 240, 255))
            key_r = key_surf.get_rect(center=tag_rect.center)
            icon_surf.blit(key_surf, key_r)

            # 6. Overlay Putaran COOLDOWN & Hitung Mundur Waktu
            if sk['cd'] > 0 and sk['cd_max'] > 0:
                cd_pct  = sk['cd'] / sk['cd_max']
                cd_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                # Gelapkan seluruh ikon
                pygame.draw.rect(cd_surf, (0, 0, 0, 160), (0, 0, icon_size, icon_size), border_radius=10)

                # Pie sweep jam cooldown
                r2 = circle_r + 2
                start_ang = -math.pi / 2
                end_ang   = start_ang + 2 * math.pi * cd_pct
                steps = max(2, int(32 * cd_pct))
                arc_pts = [(circle_cx, circle_cy)]
                for s in range(steps + 1):
                    a = start_ang + (end_ang - start_ang) * s / steps
                    arc_pts.append((circle_cx + math.cos(a) * r2, circle_cy + math.sin(a) * r2))
                if len(arc_pts) >= 3:
                    pygame.draw.polygon(cd_surf, (20, 20, 35, 180), arc_pts)

                # Teks Angka Detik Cooldown Jelas di Tengah
                cd_txt  = f'{sk["cd"]:.1f}s'
                cd_font = pygame.font.SysFont('segoe ui', 12, bold=True)
                cd_ts   = cd_font.render(cd_txt, True, (255, 255, 255))
                cd_tr   = cd_ts.get_rect(center=(circle_cx, circle_cy))
                # Shadow teks agar terbaca jelas
                cd_sh   = cd_font.render(cd_txt, True, (0, 0, 0))
                cd_surf.blit(cd_sh, (cd_tr.x + 1, cd_tr.y + 1))
                cd_surf.blit(cd_ts, cd_tr)
                icon_surf.blit(cd_surf, (0, 0))

            # 7. Efek Status Aktif (Sedang Menghilang / Sedang Dash)
            if i == 1 and sk['active']:
                vt_font = pygame.font.SysFont('segoe ui', 12, bold=True)
                vt_txt = f'{self.player.skill2_timer:.1f}s'
                vt_surf = vt_font.render(vt_txt, True, (60, 240, 255))
                vt_r = vt_surf.get_rect(center=(circle_cx, circle_cy))
                vt_sh = vt_font.render(vt_txt, True, (0, 0, 0))
                icon_surf.blit(vt_sh, (vt_r.x + 1, vt_r.y + 1))
                icon_surf.blit(vt_surf, vt_r)

            surf.blit(icon_surf, (ix, iy))

    def render(self):
        game_surf = pygame.Surface((GAME_AREA_WIDTH, SCREEN_HEIGHT))

        if self.state == 'PLAY':
            self.map.draw(game_surf, self.player)

            # Target Ambush Visual Reticle saat Skill 2 (Vanish) Aktif & Dalam Jangkauan Serangan Meningkat (85px)
            if self.player.skill2_active:
                curr_monster = self.map.monsters.get(self.current_room)
                if curr_monster and curr_monster.state != 'dead':
                    dm = distance((self.player.pos.x, self.player.pos.y), (curr_monster.pos.x, curr_monster.pos.y))
                    if dm <= 85.0:
                        ticks = pygame.time.get_ticks()
                        # Cincin target membidik cyan berdenyut di sekitar monster
                        pulse_r = int(curr_monster.radius + 6 + abs(math.sin(ticks * 0.012)) * 4)
                        pygame.draw.circle(game_surf, (40, 230, 255), (int(curr_monster.pos.x), int(curr_monster.pos.y)), pulse_r, 2)

                        # Indikator teks [SPASI] SERANG di atas monster
                        tgt_font = pygame.font.SysFont('segoe ui', 11, bold=True)
                        tgt_txt = tgt_font.render("[SPASI] SERANG!", True, (60, 240, 255))
                        tgt_rect = tgt_txt.get_rect(center=(int(curr_monster.pos.x), int(curr_monster.pos.y - curr_monster.radius - 14)))
                        bg_r = tgt_rect.inflate(12, 6)
                        b_surf = pygame.Surface((bg_r.width, bg_r.height), pygame.SRCALPHA)
                        pygame.draw.rect(b_surf, (15, 25, 40, 220), b_surf.get_rect(), border_radius=4)
                        pygame.draw.rect(b_surf, (60, 240, 255), b_surf.get_rect(), 1, border_radius=4)
                        game_surf.blit(b_surf, bg_r.topleft)
                        game_surf.blit(tgt_txt, tgt_rect)

            # Gambar Cakaran Monster
            for cm in self.claw_marks:
                cm.draw(game_surf)

            # Gambar Busur Tebasan Sabit Perak-Emas
            for sa in self.slash_arcs:
                sa.draw(game_surf)

            # Gambar Percikan Partikel
            for spk in self.sparks:
                spk.draw(game_surf)

            self.draw_hud(game_surf)
            self.draw_skills_hud(game_surf)

        elif self.state == 'VICTORY':
            game_surf.fill((25, 20, 35))
            for y in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.line(game_surf, (35, 28, 48), (0, y), (GAME_AREA_WIDTH, y))

            center_x = GAME_AREA_WIDTH // 2
            center_y = int(SCREEN_HEIGHT // 2 + 30 - self.victory_bounce)
            self.player.draw(game_surf, center_override=(center_x, center_y))

            for p in self.confetti:
                p.draw(game_surf)

            render_text(game_surf, "★ KEMENANGAN MUTLAK! ★", (center_x, 90), 32, COLOR_GOLD_ICON, bold=True, center=True)
            render_text(game_surf, "Ninja Bayangan Berhasil Menembus Seluruh Labirin dan Mencapai Portal!", (center_x, 135), 14, (230, 230, 255), center=True)

            stat_rect = pygame.Rect(center_x - 170, SCREEN_HEIGHT - 210, 340, 140)
            pygame.draw.rect(game_surf, (30, 25, 42), stat_rect, border_radius=8)
            pygame.draw.rect(game_surf, (80, 70, 110), stat_rect, 2, border_radius=8)
            render_text(game_surf, "- STATISTIK MISI SELESAI -", (center_x, SCREEN_HEIGHT - 195), 13, COLOR_PANEL_TITLE, bold=True, center=True)
            render_text(game_surf, f"Total Ruangan Ditembus : {sum(1 for info in self.map.rooms_info.values() if info['explored'])} / {self.map.total_rooms} Ruangan", (center_x - 140, SCREEN_HEIGHT - 170), 12, (210, 210, 230))
            render_text(game_surf, f"Tingkat Kesulitan      : {self.difficulty}", (center_x - 140, SCREEN_HEIGHT - 148), 12, (210, 210, 230))
            render_text(game_surf, f"Monster Dieksekusi     : {self.player.kill_count} Monster | Gold: {self.player.gold}", (center_x - 140, SCREEN_HEIGHT - 126), 12, COLOR_GOLD_ICON, bold=True)
            render_text(game_surf, "Tekan [R] untuk Bermain Lagi", (center_x, SCREEN_HEIGHT - 95), 14, (80, 255, 120), bold=True, center=True)

        elif self.state == 'GAMEOVER':
            game_surf.fill((18, 8, 10))
            cx = GAME_AREA_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            render_text(game_surf, "MISI GAGAL", (cx, cy - 60), 38, (240, 40, 40), bold=True, center=True)
            render_text(game_surf, "Ninja Tertangkap dan Gugur di Dalam Labirin", (cx, cy - 10), 15, (200, 160, 160), center=True)
            render_text(game_surf, f"Kills: {self.player.kill_count} | Gold: {self.player.gold} | Mode: {self.difficulty}", (cx, cy + 30), 13, (180, 180, 200), center=True)
            render_text(game_surf, "Tekan [R] untuk Mengulang dari Awal", (cx, cy + 85), 15, (100, 220, 255), bold=True, center=True)

        for dt_obj in self.damage_texts:
            dt_obj.draw(game_surf)

        # Efek Screen Shake saat serangan terjadi
        offset_x, offset_y = 0, 0
        if self.shake_intensity > 0:
            offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)

        self.screen.blit(game_surf, (offset_x, offset_y))
        self.draw_bayesian_panel(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()


if __name__ == '__main__':
    game = Game()
    game.run()
