"""
dungeon_3d_ninja.py - Game Desktop 3D "DUNGEON SURVIVAL: Special Hunters"
Engine: Ursina 3D Engine
Karakter: Ninja Assassin dengan Pedang Katana & Sudut Pandang Third-Person
Integrasi AI: Teorema Bayes (Bayesian Threat Analyzer) & Maximum Expected Utility (MEU)
Fitur: Dinding Labirin 3D dengan Deteksi Tabrakan (Wall Collision), Patroli Musuh, Senter Vision Cone 3D
"""

import sys
import os
import math
import random

# Pastikan path folder lokal dimuat paling awal
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from ursina import *
from dataset import (
    THREAT_CLASSES,
    MONSTER_STATS,
    PRIOR_PROBABILITIES,
    LIKELIHOOD_MATRIX,
    UTILITY_MATRIX,
    CLUE_TYPES
)
from ai_model import (
    BayesianThreatAnalyzer,
    ExpectedUtilityAdvisor,
    CombatChanceCalculator,
    normalize_angle
)

# =====================================================================
# 1. INISIALISASI URSINA ENGINE & WINDOW
# =====================================================================
app = Ursina()

window.title = "DUNGEON SURVIVAL: Special Hunters - 3D Ninja Edition"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True
window.color = color.rgb(12, 14, 20)

# Kunci kursor mouse untuk kontrol kamera 3D
mouse.locked = True

# Sistem Pencahayaan Dungeon 3D
AmbientLight(color=color.rgba(120, 130, 160, 0.45))
sun = DirectionalLight(shadows=False)
sun.look_at(Vec3(-1, -2, -1))

# Langit gelap atmosfer dungeon
Sky(color=color.rgb(10, 12, 16))

# Inisialisasi Model AI
bayes = BayesianThreatAnalyzer()
utility_advisor = ExpectedUtilityAdvisor(bayes)


# =====================================================================
# 2. DUNGEON LABIRINTH 3D DENGAN COLLIDER (TIDAK BISA MENEMBUS TEMBOK)
# =====================================================================
dungeon_root = Entity()

# Lantai Dungeon Utama
dungeon_floor = Entity(
    parent=dungeon_root,
    model='plane',
    scale=(70, 1, 70),
    color=color.rgb(24, 28, 38),
    texture='white_cube',
    texture_scale=(35, 35),
    collider='box'
)

# Atap Dungeon (Ceiling)
dungeon_ceiling = Entity(
    parent=dungeon_root,
    model='plane',
    scale=(70, 1, 70),
    y=6.0,
    rotation_x=180,
    color=color.rgb(14, 16, 22),
    texture='white_cube',
    texture_scale=(35, 35)
)

# Dinding Pembatas Luar (Boundary Walls)
boundary_walls = [
    Entity(parent=dungeon_root, model='cube', position=(0, 3, 35), scale=(70, 6, 2), color=color.rgb(38, 44, 58), texture='brick', collider='box'),
    Entity(parent=dungeon_root, model='cube', position=(0, 3, -35), scale=(70, 6, 2), color=color.rgb(38, 44, 58), texture='brick', collider='box'),
    Entity(parent=dungeon_root, model='cube', position=(35, 3, 0), scale=(2, 6, 70), color=color.rgb(38, 44, 58), texture='brick', collider='box'),
    Entity(parent=dungeon_root, model='cube', position=(-35, 3, 0), scale=(2, 6, 70), color=color.rgb(38, 44, 58), texture='brick', collider='box')
]

# Labirin & Pilar Ruangan Dalam 3D
interior_wall_data = [
    # Ruang Kiri Atas
    ((-18, 3, 16), (2, 6, 18)),
    ((-10, 3, 24), (16, 6, 2)),
    # Pilar Ruang Tengah
    ((-6, 3, 6), (5, 6, 5)),
    ((6, 3, 6), (5, 6, 5)),
    ((0, 3, 18), (14, 6, 2)),
    # Koridor Bawah & Sekat Penutup
    ((-14, 3, -12), (2, 6, 20)),
    ((-4, 3, -8), (18, 6, 2)),
    ((16, 3, -6), (2, 6, 22)),
    ((8, 3, -18), (16, 6, 2)),
    ((18, 3, 14), (14, 6, 2)),
    ((22, 3, -20), (4, 6, 8)),
    ((-22, 3, -4), (6, 6, 4))
]

interior_walls = []
for pos, scl in interior_wall_data:
    wall_ent = Entity(
        parent=dungeon_root,
        model='cube',
        position=pos,
        scale=scl,
        color=color.rgb(46, 54, 70),
        texture='brick',
        texture_scale=(scl[0] / 2, scl[1] / 2),
        collider='box'
    )
    interior_walls.append(wall_ent)

# Zona Penutup Semak Hijau 3D (Cover Bushes - Ninja Sembunyi)
cover_zones_data = [
    ((-26, 0.4, 26), (6, 0.8, 6)),
    ((-14, 0.4, 4), (5, 0.8, 5)),
    ((0, 0.4, -22), (6, 0.8, 6)),
    ((24, 0.4, 22), (6, 0.8, 6)),
    ((26, 0.4, -10), (5, 0.8, 5))
]

cover_zones = []
for pos, scl in cover_zones_data:
    c_box = Entity(
        parent=dungeon_root,
        model='cube',
        position=pos,
        scale=scl,
        color=color.rgba(46, 125, 75, 160),
        texture='white_cube'
    )
    cover_zones.append(c_box)


# =====================================================================
# 3. MODEL KARAKTER 3D NINJA & PEDANG KATANA
# =====================================================================
class NinjaPlayer(Entity):
    """
    Karakter Ninja 3D dengan visual kostum shinobi gelap, syal merah,
    pedang Katana, dan kamera Third-Person yang responsif.
    """
    def __init__(self, position=(0, 0, -28)):
        super().__init__(position=position)
        
        # Collider karakter untuk tabrakan fisik
        self.collider = BoxCollider(self, size=(1.0, 2.0, 1.0), center=(0, 1.0, 0))
        
        # Status Hunter Ninja
        self.hp = 100
        self.max_hp = 100
        self.gold = 0
        self.stance = "WALK"     # "WALK", "SPRINT", "CROUCH", "COVER"
        self.speed = 8.0
        self.is_attacking = False
        self.attack_cooldown = 0.0

        # --- A. PEMBUATAN MODEL 3D NINJA ---
        self.visual_root = Entity(parent=self)

        # Tubuh Ninja (Shinobi Shozoku Gelap)
        self.torso = Entity(
            parent=self.visual_root,
            model='cube',
            scale=(0.7, 0.9, 0.45),
            y=1.1,
            color=color.rgb(20, 22, 28)
        )
        # Sabuk Merah (Obi)
        self.belt = Entity(
            parent=self.visual_root,
            model='cube',
            scale=(0.72, 0.15, 0.48),
            y=0.75,
            color=color.rgb(192, 57, 43)
        )
        # Kepala Ninja & Masker
        self.head = Entity(
            parent=self.visual_root,
            model='cube',
            scale=(0.42, 0.42, 0.42),
            y=1.8,
            color=color.rgb(22, 24, 30)
        )
        # Ikat Kepala / Syal Merah (Shinobi Headband)
        self.headband = Entity(
            parent=self.head,
            model='cube',
            scale=(1.05, 0.25, 1.05),
            y=0.1,
            color=color.rgb(231, 76, 60)
        )
        # Pita Syal Menjuntai di Belakang
        self.scarf_tail = Entity(
            parent=self.headband,
            model='cube',
            scale=(0.25, 0.8, 0.1),
            position=(0, -0.4, -0.6),
            rotation_x=20,
            color=color.rgb(231, 76, 60)
        )
        # Kaki Kiri & Kanan
        self.leg_left = Entity(parent=self.visual_root, model='cube', scale=(0.25, 0.7, 0.3), position=(-0.2, 0.35, 0), color=color.rgb(18, 20, 26))
        self.leg_right = Entity(parent=self.visual_root, model='cube', scale=(0.25, 0.7, 0.3), position=(0.2, 0.35, 0), color=color.rgb(18, 20, 26))

        # --- B. SENJATA PEDANG KATANA 3D ---
        self.weapon_arm = Entity(parent=self.visual_root, position=(0.45, 1.1, 0.1))
        # Gagang Katana (Tsuka)
        self.katana_hilt = Entity(parent=self.weapon_arm, model='cube', scale=(0.06, 0.28, 0.06), y=0, color=color.rgb(30, 30, 30))
        # Pelindung Tangan (Tsuba)
        self.katana_guard = Entity(parent=self.weapon_arm, model='cube', scale=(0.22, 0.03, 0.22), y=0.15, color=color.rgb(241, 196, 15))
        # Bilah Katana Mengkilap (Ha)
        self.katana_blade = Entity(parent=self.weapon_arm, model='cube', scale=(0.04, 1.2, 0.08), position=(0, 0.75, 0), color=color.rgb(236, 240, 241))

        # Posisi awal Katana siap di sisi
        self.weapon_arm.rotation = (60, -20, -15)

        # --- C. PENGATURAN KAMERA THIRD-PERSON ---
        self.camera_pivot = Entity(parent=self, y=1.8)
        camera.parent = self.camera_pivot
        camera.position = (0, 1.2, -4.5)  # Sudut pandang over-the-shoulder
        camera.rotation_x = 12

    def update_movement(self, dt):
        """
        Pergerakan Ninja dengan Deteksi Tabrakan Dinding (Wall Collision).
        Mencegah Ninja menembus tembok dengan raycasting terarah.
        """
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Rotasi Kamera & Karakter dengan Mouse
        self.rotation_y += mouse.velocity[0] * 120
        self.camera_pivot.rotation_x -= mouse.velocity[1] * 100
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -45, 45)

        # Cek Stance (Sprint / Crouch / Cover)
        if held_keys['shift']:
            self.stance = "SPRINT"
            self.speed = 12.0
        elif held_keys['control'] or held_keys['c']:
            self.stance = "CROUCH"
            self.speed = 4.0
        else:
            self.stance = "WALK"
            self.speed = 7.5

        # Cek Zona Sembunyi (Cover)
        is_in_cover = False
        for c_box in cover_zones:
            if abs(self.x - c_box.x) < c_box.scale_x / 2 and abs(self.z - c_box.z) < c_box.scale_z / 2:
                is_in_cover = True
                break
        if is_in_cover:
            self.stance = "COVER"
            # Visual semitransparan saat menyamar
            self.visual_root.alpha = 0.5
        else:
            self.visual_root.alpha = 1.0

        # Vektor Input WASD
        move_dir = Vec3(0, 0, 0)
        if held_keys['w'] or held_keys['up arrow']:
            move_dir += self.forward
        if held_keys['s'] or held_keys['down arrow']:
            move_dir -= self.forward
        if held_keys['d'] or held_keys['right arrow']:
            move_dir += self.right
        if held_keys['a'] or held_keys['left arrow']:
            move_dir -= self.right

        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalized()
            
            # --- DETEKSI TABRAKAN DINDING RAYCAST (ANTI TEMBUS TEMBOK) ---
            ray_origin = self.position + Vec3(0, 1.0, 0)
            
            # Cek sumbu X
            step_x = move_dir.x * self.speed * dt
            if step_x != 0:
                dir_x = Vec3(1 if step_x > 0 else -1, 0, 0)
                hit_x = raycast(ray_origin, dir_x, distance=abs(step_x) + 0.7, ignore=[self, dungeon_floor, dungeon_ceiling], traverse_target=dungeon_root)
                if not hit_x.hit:
                    self.x += step_x

            # Cek sumbu Z
            step_z = move_dir.z * self.speed * dt
            if step_z != 0:
                dir_z = Vec3(0, 0, 1 if step_z > 0 else -1)
                hit_z = raycast(ray_origin, dir_z, distance=abs(step_z) + 0.7, ignore=[self, dungeon_floor, dungeon_ceiling], traverse_target=dungeon_root)
                if not hit_z.hit:
                    self.z += step_z

            # Efek goyangan syal merah saat berlari
            self.scarf_tail.rotation_x = 20 + math.sin(time.time() * 15) * 25
        else:
            self.scarf_tail.rotation_x = 20

    def slash_attack(self):
        """Animasi Tebasan Pedang Katana (Katana Slash Arc)."""
        if self.is_attacking or self.attack_cooldown > 0:
            return
        self.is_attacking = True
        self.attack_cooldown = 0.35

        # Animasi ayunan Katana ke depan secara cepat
        self.weapon_arm.animate_rotation((-45, 80, -30), duration=0.1, curve=curve.out_expo)
        invoke(self._reset_weapon_pos, delay=0.15)

    def _reset_weapon_pos(self):
        self.weapon_arm.animate_rotation((60, -20, -15), duration=0.15, curve=curve.in_out_quad)
        self.is_attacking = False


# Inisialisasi Objek Pemain Ninja
ninja = NinjaPlayer(position=(0, 0, -28))


# =====================================================================
# 4. KELAS MUSUH 3D & SENTER KERUCUT PANDANG (VISION CONE)
# =====================================================================
class Monster3D(Entity):
    """
    Musuh 3D yang berpatroli dengan senter penglihatan 3D (Vision Cone).
    Mendukung status PATROL, SUSPICIOUS, ALERT/CHASE.
    """
    def __init__(self, position, monster_type, waypoints):
        super().__init__(position=position)
        self.monster_type = monster_type
        self.stats = MONSTER_STATS.get(monster_type, MONSTER_STATS["Goblin Scout"])
        self.hp = self.stats["hp"]
        self.max_hp = self.stats["hp"]
        self.damage = self.stats["damage"]
        self.speed = self.stats["speed"] * 0.9
        self.chase_speed = self.stats["chase_speed"] * 1.1
        self.vision_dist = self.stats["vision_radius"] / 18.0
        self.vision_angle = self.stats["vision_angle"]
        self.gold_reward = self.stats["gold"]
        self.is_alive = True

        self.waypoints = [Vec3(w[0], 0, w[1]) for w in waypoints]
        self.current_wp_idx = 0
        self.state = "PATROL"  # "PATROL", "SUSPICIOUS", "ALERT"
        self.detection_meter = 0.0
        self.attack_cooldown = 0.0

        # Model Tubuh Monster
        self.body = Entity(
            parent=self,
            model='cube',
            scale=(1.2, 1.8, 1.2),
            y=0.9,
            color=color.rgb(*self.stats["color"]),
            collider='box'
        )
        # Mata / Tanduk Monster
        self.eye = Entity(parent=self.body, model='cube', scale=(0.8, 0.2, 0.2), position=(0, 0.3, 0.55), color=color.red)

        # Senter Vision Cone 3D
        self.cone = Entity(
            parent=self,
            model='cone',
            color=color.rgba(255, 220, 0, 45),
            position=(0, 1.0, self.vision_dist / 2),
            rotation_x=90,
            scale=(self.vision_dist * 0.9, self.vision_dist, self.vision_dist * 0.9)
        )

        # Indikator Status di Atas Kepala
        self.status_text = Text(
            parent=self,
            text="",
            position=(0, 2.5, 0),
            scale=14,
            billboard=True,
            origin=(0, 0),
            color=color.yellow
        )

    def update_ai(self, dt, target_player):
        if not self.is_alive:
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        dist_to_player = distance(self.position, target_player.position)
        
        # Hitung sudut hadap ke pemain
        to_player = (target_player.position - self.position).normalized()
        angle_diff = math.degrees(math.acos(clamp(self.forward.dot(to_player), -1.0, 1.0)))

        # 1. Cek Deteksi Pandangan
        in_vision = False
        if dist_to_player < self.vision_dist and angle_diff < self.vision_angle / 2:
            # Raycast line-of-sight terhadap dinding
            los_ray = raycast(self.position + Vec3(0, 1.2, 0), to_player, distance=dist_to_player, ignore=[self, self.body, target_player], traverse_target=dungeon_root)
            if not los_ray.hit:
                in_vision = True

        # Stance multiplier
        multiplier = 0.1 if target_player.stance == "COVER" else 0.4 if target_player.stance == "CROUCH" else 1.5 if target_player.stance == "SPRINT" else 1.0

        if in_vision:
            self.detection_meter = min(1.0, self.detection_meter + 2.2 * multiplier * dt)
            if self.detection_meter >= 0.7:
                self.state = "ALERT"
            elif self.detection_meter >= 0.3 and self.state != "ALERT":
                self.state = "SUSPICIOUS"
        else:
            self.detection_meter = max(0.0, self.detection_meter - 0.4 * dt)
            if self.detection_meter <= 0.1 and self.state == "SUSPICIOUS":
                self.state = "PATROL"

        # 2. Update Warna Senter & Teks Status
        if self.state == "ALERT":
            self.cone.color = color.rgba(255, 30, 30, 80)
            self.status_text.text = "!"
            self.status_text.color = color.red
            # Kejar Pemain Ninja
            self.look_at_2d(target_player.position, 'y')
            self.position += self.forward * self.chase_speed * dt
            # Serang jika dalam jangkauan melee
            if dist_to_player < 2.0 and self.attack_cooldown <= 0:
                target_player.hp = max(0, target_player.hp - self.damage)
                self.attack_cooldown = 1.0
                ninja.visual_root.blink(color.red, duration=0.2)
        elif self.state == "SUSPICIOUS":
            self.cone.color = color.rgba(255, 140, 0, 60)
            self.status_text.text = "?"
            self.status_text.color = color.yellow
            self.look_at_2d(target_player.position, 'y')
        else:
            self.cone.color = color.rgba(255, 220, 0, 35)
            self.status_text.text = ""
            self.patrol(dt)

    def patrol(self, dt):
        if not self.waypoints:
            return
        target_wp = self.waypoints[self.current_wp_idx]
        to_wp = target_wp - self.position
        to_wp.y = 0
        if to_wp.length() < 1.2:
            self.current_wp_idx = (self.current_wp_idx + 1) % len(self.waypoints)
        else:
            self.look_at_2d(target_wp, 'y')
            self.position += self.forward * self.speed * dt

    def take_damage(self, amount, is_assassinate=False):
        self.hp -= amount
        # Partikel tebasan
        self.body.blink(color.white, duration=0.15)
        if self.hp <= 0:
            self.is_alive = False
            self.enabled = False
            ninja.gold += self.gold_reward


# Daftar Musuh 3D di Dalam Dungeon
enemies_3d = [
    Monster3D(position=(-12, 0, 16), monster_type="Goblin Scout", waypoints=[(-12, 16), (-24, 16), (-24, 28), (-12, 28)]),
    Monster3D(position=(16, 0, 18), monster_type="Orc Sentry", waypoints=[(16, 18), (28, 18), (28, 6), (16, 6)]),
    Monster3D(position=(-18, 0, -18), monster_type="Shadow Stalker", waypoints=[(-18, -18), (-28, -18), (-28, -6), (-18, -6)]),
    Monster3D(position=(12, 0, -18), monster_type="Dungeon Warden", waypoints=[(12, -18), (24, -18), (24, -28), (12, -28)])
]


# =====================================================================
# 5. TITIK BUKTI PETUNJUK 3D (BAYESIAN CLUE SPOTS)
# =====================================================================
class ClueSpot3D(Entity):
    """Bola rune 3D berdenyut di lantai untuk investigasi Teorema Bayes."""
    def __init__(self, position, clue_type, label):
        super().__init__(position=position)
        self.clue_type = clue_type
        self.label = label
        self.discovered = False

        # Rune Orb 3D
        self.orb = Entity(parent=self, model='sphere', scale=0.7, y=0.6, color=color.cyan)
        self.ring = Entity(parent=self, model='torus', scale=(1.1, 0.1, 1.1), y=0.6, color=color.white)
        self.prompt = Text(parent=self, text=f"[E] {label}", scale=10, billboard=True, y=1.6, origin=(0, 0), color=color.cyan)

    def update_anim(self, dt):
        if not self.discovered:
            self.orb.rotation_y += 60 * dt
            self.orb.y = 0.6 + math.sin(time.time() * 3) * 0.15
            self.ring.rotation_x += 45 * dt

    def collect(self):
        if not self.discovered:
            self.discovered = True
            self.orb.color = color.gray
            self.ring.enabled = False
            self.prompt.text = f"[OK] {self.label}"
            self.prompt.color = color.gray
            bayes.add_clue(self.clue_type)


# Penempatan 5 Titik Petunjuk 3D
clue_spots_3d = [
    ClueSpot3D(position=(-10, 0, 10), clue_type="scratch_marks", label="Bekas Cakar"),
    ClueSpot3D(position=(0, 0, 14), clue_type="heavy_footsteps", label="Jejak Kaki Berat"),
    ClueSpot3D(position=(-8, 0, -12), clue_type="mana_aura", label="Residu Sihir"),
    ClueSpot3D(position=(10, 0, -8), clue_type="blood_trail", label="Ceceran Darah"),
    ClueSpot3D(position=(20, 0, 20), clue_type="rattling_armor", label="Gesekan Zirah")
]


# =====================================================================
# 6. PANEL HUD 2D & REKOMENDASI TIKTIK AI (BAYES & MEU)
# =====================================================================
hud_canvas = Entity(parent=camera.ui)

# Status Pemain Kiri Atas
hp_bar_bg = Entity(parent=hud_canvas, model='quad', scale=(0.32, 0.04), position=(-0.68, 0.44), color=color.rgb(30, 30, 30))
hp_bar_fill = Entity(parent=hud_canvas, model='quad', scale=(0.30, 0.03), position=(-0.68, 0.44), color=color.green)
hp_label = Text(parent=hud_canvas, text="NINJA HP: 100/100", position=(-0.83, 0.455), scale=1.0, color=color.white)

gold_label = Text(parent=hud_canvas, text="GOLD: 0", position=(-0.83, 0.40), scale=1.1, color=color.gold)
stance_label = Text(parent=hud_canvas, text="STANCE: WALK", position=(-0.83, 0.36), scale=1.0, color=color.cyan)

# Indikator Eksekusi Assassinate di Tengah Layar
assassinate_prompt = Text(parent=hud_canvas, text="", position=(0, -0.2), origin=(0, 0), scale=1.6, color=color.gold)

# Panel Kanan AI Tactical Advisor
ai_bg = Entity(parent=hud_canvas, model='quad', scale=(0.42, 0.94), position=(0.74, 0), color=color.rgba(18, 22, 30, 230))
ai_title = Text(parent=hud_canvas, text="AI TACTICAL ADVISOR", position=(0.55, 0.44), scale=1.1, color=color.cyan)
ai_subtitle = Text(parent=hud_canvas, text="Bayes Probabilities & MEU Decision", position=(0.55, 0.41), scale=0.75, color=color.light_gray)

# Baris Probabilitas Bayes
bayes_row_texts = []
for idx, threat in enumerate(THREAT_CLASSES):
    t_name = Text(parent=hud_canvas, text=f"{threat}: 25%", position=(0.55, 0.35 - idx * 0.045), scale=0.85, color=color.white)
    bayes_row_texts.append(t_name)

# Status Bukti / Clue
clue_status_title = Text(parent=hud_canvas, text="Bukti Ditemukan:", position=(0.55, 0.15), scale=0.85, color=color.yellow)
clue_status_body = Text(parent=hud_canvas, text="Belum ada (Prior)", position=(0.55, 0.11), scale=0.75, color=color.light_gray)

# Rekomendasi Expected Utility (MEU)
eu_title_label = Text(parent=hud_canvas, text="Rekomendasi Taktik (MEU):", position=(0.55, 0.03), scale=0.85, color=color.green)
eu_action_box = Entity(parent=hud_canvas, model='quad', scale=(0.38, 0.12), position=(0.74, -0.06), color=color.rgba(30, 40, 55, 220))
eu_action_label = Text(parent=hud_canvas, text="Analisis...", position=(0.56, -0.04), scale=0.9, color=color.white)
eu_score_label = Text(parent=hud_canvas, text="Score: +0.0 pts", position=(0.56, -0.09), scale=0.8, color=color.yellow)

# Panduan Tombol di Bawah
controls_help = Text(
    parent=hud_canvas,
    text="WASD: Gerak | MOUSE: Lihat | SHIFT: Sprint | CTRL: Mengendap | SPASI: Serang/Assassinate | E: Clue | TAB: HUD",
    position=(-0.85, -0.46),
    scale=0.75,
    color=color.light_gray
)


# =====================================================================
# 7. GAME LOOP UPDATE & EVENT INTERACTION
# =====================================================================
def update():
    dt = time.dt

    # 1. Update Ninja Movement
    ninja.update_movement(dt)

    # 2. Update Clue Spots 3D
    for c in clue_spots_3d:
        c.update_anim(dt)

    # 3. Update AI Musuh 3D & Deteksi Assassination
    can_assassinate = False
    target_assassinate = None

    for enemy in enemies_3d:
        if enemy.is_alive:
            enemy.update_ai(dt, ninja)
            
            # Cek jangkauan pembunuhan senyap (Assassination Range)
            dist = distance(ninja.position, enemy.position)
            if dist < 3.2:
                # Evaluasi sudut hadap relatif
                to_player = (ninja.position - enemy.position).normalized()
                angle_dot = enemy.forward.dot(to_player)
                
                # Jika berada di belakang musuh (angle_dot < 0) dan musuh belum alert
                if angle_dot < -0.1 and enemy.state != "ALERT":
                    can_assassinate = True
                    target_assassinate = enemy

    # Tampilkan prompt eksekusi instan
    if can_assassinate:
        assassinate_prompt.text = "[SPASI] SILENT ASSASSINATE!"
    else:
        assassinate_prompt.text = ""

    # 4. Update HUD Status
    hp_ratio = max(0.0, ninja.hp / ninja.max_hp)
    hp_bar_fill.scale_x = 0.30 * hp_ratio
    hp_label.text = f"NINJA HP: {int(ninja.hp)}/{ninja.max_hp}"
    gold_label.text = f"GOLD: {ninja.gold}"
    stance_label.text = f"STANCE: {ninja.stance}"
    stance_label.color = color.green if ninja.stance == "COVER" else color.cyan if ninja.stance == "CROUCH" else color.yellow if ninja.stance == "SPRINT" else color.white

    # 5. Update Teorema Bayes & Expected Utility di Panel HUD
    posteriors = bayes.calculate_posterior()
    for idx, threat in enumerate(THREAT_CLASSES):
        prob = posteriors.get(threat, 0.25)
        bayes_row_texts[idx].text = f"{threat}: {int(prob * 100)}%"

    # Update Bukti Terkumpul
    if bayes.observed_clues:
        clue_names = ", ".join([c.replace('_', ' ').title() for c in bayes.observed_clues])
        clue_status_body.text = clue_names[:28] + ("..." if len(clue_names) > 28 else "")
    else:
        clue_status_body.text = "Belum ada (Prior)"

    # Update Taktik Terbaik (MEU)
    tactics = utility_advisor.evaluate_tactics(posteriors)
    best_tactic = tactics[0]
    eu_action_label.text = f">> {best_tactic['action']}"
    eu_score_label.text = f"Score: {best_tactic['eu']:+.1f} ({best_tactic['status']})"
    eu_action_label.color = color.rgb(*best_tactic['color'])

    # Cek Game Over
    if ninja.hp <= 0:
        assassinate_prompt.text = "MISSION FAILED! TEKAN [R] RESTART"
        assassinate_prompt.color = color.red


def input(key):
    # Toggle Cursor Mouse dengan ESC
    if key == 'escape':
        mouse.locked = not mouse.locked

    # Restart Permainan
    if key == 'r' and ninja.hp <= 0:
        ninja.hp = ninja.max_hp
        ninja.position = (0, 0, -28)
        ninja.gold = 0
        bayes.reset()
        for e in enemies_3d:
            e.hp = e.max_hp
            e.is_alive = True
            e.enabled = True
            e.state = "PATROL"
        for c in clue_spots_3d:
            c.discovered = False
            c.orb.color = color.cyan
            c.ring.enabled = True
            c.prompt.text = f"[E] {c.label}"
            c.prompt.color = color.cyan

    # Toggle Tampilan HUD AI dengan TAB
    if key == 'tab':
        ai_bg.enabled = not ai_bg.enabled
        ai_title.enabled = not ai_title.enabled
        ai_subtitle.enabled = not ai_subtitle.enabled
        for t in bayes_row_texts:
            t.enabled = not t.enabled
        clue_status_title.enabled = not clue_status_title.enabled
        clue_status_body.enabled = not clue_status_body.enabled
        eu_title_label.enabled = not eu_title_label.enabled
        eu_action_box.enabled = not eu_action_box.enabled
        eu_action_label.enabled = not eu_action_label.enabled
        eu_score_label.enabled = not eu_score_label.enabled

    # Ambil Clue dengan tombol E
    if key == 'e':
        for c in clue_spots_3d:
            if not c.discovered and distance(ninja.position, c.position) < 3.2:
                c.collect()
                break

    # Serangan Pedang Katana / Assassinate dengan Spasi atau Klik Kiri
    if key == 'space' or key == 'left mouse down':
        ninja.slash_attack()

        # Cek apakah ada musuh yang terkena serangan
        for enemy in enemies_3d:
            if enemy.is_alive and distance(ninja.position, enemy.position) < 3.5:
                to_player = (ninja.position - enemy.position).normalized()
                angle_dot = enemy.forward.dot(to_player)

                # Eksekusi Assassination dari belakang
                if angle_dot < -0.1 and enemy.state != "ALERT":
                    enemy.take_damage(enemy.max_hp, is_assassinate=True)
                else:
                    # Serangan biasa
                    enemy.take_damage(45, is_assassinate=False)
                    enemy.state = "ALERT"
                break


# =====================================================================
# 8. MENJALANKAN APLIKASI GAME 3D URSINA
# =====================================================================
if __name__ == '__main__':
    app.run()

