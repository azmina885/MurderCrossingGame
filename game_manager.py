"""
game_manager.py
Murder Crossing Game: The Blackwood Case
SWC3643 - Python Programming Language Project

HOW TO ADD YOUR OWN CHARACTER IMAGES
--------------------------------------
1. Create a folder called  images/  next to this file.
2. Save each character image as a PNG with EXACTLY these filenames:
       detective.png
       butler.png
       maid.png
       doctor.png
       nephew.png
       knife.png
       letter.png
       key.png
3. Recommended size: 75 × 90 pixels (or any size — they are auto-scaled).
4. If an image file is missing, the game falls back to the coloured-card drawing.

BACKGROUND IMAGES
------------------
   images/bg_menu.png    — used on the Main Menu  (1.png → rename to bg_menu.png)
   images/bg_opening.png — used on the Opening / Story screen (2.png → rename to bg_opening.png)
"""

import os
import pygame
import sys

from boat  import Boat
from level import create_level

# ── Colours ────────────────────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
DARK_BG    = (12,  8,   25)
OPENING_BG = (18,  14,  45)
RIVER_D    = (15,  40,  90)
RIVER_L    = (30,  75,  150)
BANK_EARTH = (55,  35,  12)
BANK_GRASS = (25,  65,  18)
GOLD       = (255, 200, 50)
RED        = (210, 50,  50)
GREEN      = (50,  185, 80)
GREY       = (140, 140, 140)
PANEL      = (18,  12,  38)
DARK_RED   = (120, 20,  20)
CREAM      = (245, 240, 220)
TEAL       = (40,  175, 160)


# ── Image / asset loader ──────────────────────────────────────────────────

def _img_path(*parts):
    """Return absolute path inside the  images/  folder next to this file."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "images", *parts)


def _load_bg(filename, target_w, target_h):
    """Load a background image and scale it to fill the window. Returns None on failure."""
    path = _img_path(filename)
    if not os.path.isfile(path):
        return None
    try:
        surf = pygame.image.load(path).convert()
        return pygame.transform.smoothscale(surf, (target_w, target_h))
    except Exception:
        return None


def _load_char_image(filename, w=55, h=70):
    """Load a character / evidence portrait and scale it. Returns None on failure."""
    path = _img_path(filename)
    if not os.path.isfile(path):
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(surf, (w, h))
    except Exception:
        return None


# Map entity names → image filenames
ENTITY_IMAGES = {
    "Detective James": "detective.png",
    "Butler":          "butler.png",
    "Maid":            "maid.png",
    "Doctor":          "doctor.png",
    "Nephew":          "nephew.png",
    "Knife":           "knife.png",
    "Secret Letter":   "letter.png",
    "Safe Key":        "key.png",
}


class GameManager:
    """
    Central controller for all game states.

    States
    ------
    MENU | HOW_TO_PLAY | CREDITS | OPENING | PLAYING |
    PAUSED | LEVEL_CLEAR | WIN | LOSE
    """

    MAX_LEVELS = 3

    def __init__(self, screen, fonts):
        self.screen = screen
        self.W      = screen.get_width()
        self.H      = screen.get_height()
        self.fonts  = fonts   # keys: big, medium, small, tiny

        self.state  = "MENU"
        self.lang   = "EN"

        # Sound toggle — True = on, False = muted
        self.sound_on   = True
        self._init_sound()

        # Rain animation for opening screen
        import random
        self._rain_drops = [
            [random.randint(0, 960), random.randint(0, 680),
             random.uniform(1.5, 3.5), random.uniform(0.3, 0.8)]
            for _ in range(40)
        ]

        # Level / game state
        self.level_num      = 1
        self.level          = None
        self.boat           = None
        self.unlocked_levels = 1
        self.level_select_num = 1

        self.timer   = 0
        self._ms_acc = 0

        self.score       = 0
        self.total_score = 0
        self.move_count  = 0

        # Selection
        self.selection_index = -1
        self.popup_entity    = None
        self.popup_timer     = 0

        # Temporary feedback message
        self.msg       = ""
        self.msg_timer = 0

        # Opening / story pagination
        self.open_page = 0

        # Visual
        self.wave      = 0
        self.rain_seed = 0

        # ── Load background images ─────────────────────────────────────────
        self.bg_menu    = _load_bg("bg_menu.png",    self.W, self.H)
        self.bg_opening = _load_bg("bg_opening.png", self.W, self.H)

        # ── Pre-load character images ──────────────────────────────────────
        self.char_images = {}
        for name, fname in ENTITY_IMAGES.items():
            img = _load_char_image(fname)
            if img:
                self.char_images[name] = img

        # ── Pre-load UI icons ──────────────────────────────────────────────
        self.icon_checkmark = _load_char_image("checkmark.png", w=28, h=28)
        self.icon_over      = _load_char_image("over_icon.png", w=72, h=72)
        self.icon_guilty    = _load_char_image("guilty.png",    w=120, h=60)
        self.icon_objective = _load_char_image("objective.png", w=36, h=36)
        self.icon_control   = _load_char_image("control.png",   w=36, h=36)
        self.icon_rules     = _load_char_image("rules.png",     w=36, h=36)

        # ── Bilingual strings ──────────────────────────────────────────────
        self.TR = {
            "EN": {
                "start":       "Start Game",
                "how":         "How to play",
                "exit":        "Exit",
                "pause":       "— PAUSED —",
                "resume":      "RESUME  [P]",
                "restart":     "RESTART  [R]",
                "menu":        "MENU  [ESC]",
                "score":       "SCORE",
                "moves":       "MOVES",
                "timer":       "TIME",
                "next":        "NEXT LEVEL  [ENTER]",
                "end":         "MAIN MENU  [ENTER]",
                "lang_lbl":    "English",
                "lang_switch": "Bahasa Melayu",
                "win_t":       "CASE CLOSED",
                "lose_t":      "INVESTIGATION FAILED",
                "hint_sail":   "ENTER = sail  |  A/D = select  |  SPACE = load/unload",
                "back":        "Back",
                "next_btn":    "Next",
                "story":       "The story:",
                "level_lbl":   "Level",
                "sel_title":   "SELECT LEVEL",
                "locked":      "LOCKED",
                "play_btn":    "PLAY",
                "instr_title": "Instructions",
                "instr_rule":  "RULES FOR THIS LEVEL",
                "instr_note":  "Detective James must be on the boat to sail.",
                "instr_cap":   "Boat capacity: Detective + 1 only.",
                "instr_start": "START GAME",
                "instr_back":  "Back",
                "diff_easy":   "Easy",
                "diff_med":    "Medium",
                "diff_hard":   "Hard",
            },
            "MY": {
                "start":       "Mula Permainan",
                "how":         "Cara Bermain",
                "exit":        "Keluar",
                "pause":       "— BERHENTI —",
                "resume":      "TERUSKAN  [P]",
                "restart":     "MULA SEMULA  [R]",
                "menu":        "MENU  [ESC]",
                "score":       "MARKAH",
                "moves":       "LANGKAH",
                "timer":       "MASA",
                "next":        "PERINGKAT SETERUSNYA  [ENTER]",
                "end":         "MENU UTAMA  [ENTER]",
                "lang_lbl":    "Bahasa Melayu",
                "lang_switch": "English",
                "win_t":       "KES SELESAI",
                "lose_t":      "SIASATAN GAGAL",
                "hint_sail":   "ENTER = belayar  |  A/D = pilih  |  SPACE = naik/turun",
                "back":        "Kembali",
                "next_btn":    "Seterusnya",
                "story":       "Cerita:",
                "level_lbl":   "Peringkat",
                "sel_title":   "PILIH PERINGKAT",
                "locked":      "TERKUNCI",
                "play_btn":    "MAIN",
                "instr_title": "Arahan",
                "instr_rule":  "PERATURAN PERINGKAT INI",
                "instr_note":  "Detektif James mesti berada di bot untuk belayar.",
                "instr_cap":   "Kapasiti bot: Detektif + 1 sahaja.",
                "instr_start": "MULA PERMAINAN",
                "instr_back":  "Kembali",
                "diff_easy":   "Mudah",
                "diff_med":    "Sederhana",
                "diff_hard":   "Susah",
            },
        }

        # ── Entity name translations ───────────────────────────────────────
        self.ENTITY_NAMES = {
            "EN": {
                "Detective James": "Detective James",
                "Butler":          "Butler",
                "Maid":            "Maid",
                "Doctor":          "Doctor",
                "Nephew":          "Nephew",
                "Knife":           "Knife",
                "Secret Letter":   "Secret Letter",
                "Safe Key":        "Safe Key",
            },
            "MY": {
                "Detective James": "Detektif James",
                "Butler":          "Butler",
                "Maid":            "Pembantu Rumah",
                "Doctor":          "Doktor",
                "Nephew":          "Anak Saudara",
                "Knife":           "Pisau",
                "Secret Letter":   "Surat Rahsia",
                "Safe Key":        "Kunci Peti Besi",
            },
        }

        # ── Bilingual opening-story text ───────────────────────────────────
        self.STORY_PAGES = {
            1: {
                "EN": [
                    "Around 10:40 pm at the BLACKWOOD MANSION, a scream echoes through\n"
                    "the mansion. Mr. Blackwood is found dead in his study room.\n"
                    "As the detective arrived at the location, something happened\n"
                    "whereas the bridge to town collapsed. To further investigate,\n"
                    "the detective must transport all suspects and evidence across\n"
                    "the river to the nearest police station.\n"
                    "So be careful... someone is hiding the truth.",
                ],
                "MY": [
                    "Kira-kira pukul 10:40 malam di BLACKWOOD MANSION, jeritan bergema\n"
                    "di seluruh rumah. Encik Blackwood ditemui mati di bilik studinya.\n"
                    "Ketika detektif tiba di lokasi, sesuatu berlaku —\n"
                    "jambatan ke pekan telah runtuh. Untuk menyiasat lebih lanjut,\n"
                    "detektif mesti membawa semua suspek dan bukti merentasi\n"
                    "sungai ke balai polis terdekat.\n"
                    "Berhati-hati... seseorang sedang menyembunyikan kebenaran.",
                ],
            },
            2: {
                "EN": [
                    "The investigation continues at BLACKWOOD MANSION.\n"
                    "While searching Mr. Blackwood's study, Detective James discovers\n"
                    "a secret letter hidden inside a locked desk drawer.\n"
                    "The letter contains crucial information about a change\n"
                    "to Mr. Blackwood's will — someone stood to lose everything.\n"
                    "The Maid has been seen near the desk and knows what is inside.\n"
                    "If left alone with the letter, she may destroy it.\n"
                    "A Doctor has also arrived late at night as a new suspect.\n"
                    "Transport all suspects and evidence safely across the river.\n"
                    "Stay alert — the killer is still among them.",
                ],
                "MY": [
                    "Siasatan diteruskan di BLACKWOOD MANSION.\n"
                    "Semasa menggeledah bilik study, Detektif James menemui\n"
                    "sepucuk surat rahsia tersembunyi dalam laci meja yang terkunci.\n"
                    "Surat itu mengandungi maklumat penting tentang perubahan wasiat\n"
                    "Encik Blackwood — seseorang bakal kehilangan segalanya.\n"
                    "Pembantu Rumah telah dilihat berhampiran meja dan tahu isinya.\n"
                    "Jika dibiarkan bersendirian dengan surat itu, dia mungkin memusnahkannya.\n"
                    "Seorang Doktor juga tiba lewat malam sebagai suspek baru.\n"
                    "Bawa semua suspek dan bukti merentasi sungai dengan selamat.\n"
                    "Berwaspada — pembunuh masih berada di antara mereka.",
                ],
            },
            3: {
                "EN": [
                    "The case takes a dark turn at BLACKWOOD MANSION.\n"
                    "A Safe Key has been found — it unlocks Blackwood's private vault\n"
                    "believed to hold the final proof of the murderer's identity.\n"
                    "The Nephew has arrived, desperate to access the vault before police.\n"
                    "The Maid still threatens to destroy the Secret Letter.\n"
                    "The Butler remains dangerous near the Knife.\n"
                    "Three deadly combinations must be avoided at all times.\n"
                    "Transport all five suspects and three pieces of evidence safely.\n"
                    "This is your final chance. Justice depends on you.",
                ],
                "MY": [
                    "Kes ini mengambil giliran gelap di BLACKWOOD MANSION.\n"
                    "Sebuah Kunci Peti Besi ditemui — ia membuka peti simpanan Blackwood\n"
                    "yang dipercayai menyimpan bukti muktamad identiti pembunuh.\n"
                    "Anak Saudara tiba terdesak untuk mengakses peti besi sebelum polis.\n"
                    "Pembantu Rumah masih mengancam untuk memusnahkan Surat Rahsia.\n"
                    "Butler kekal berbahaya berhampiran Pisau.\n"
                    "Tiga kombinasi merbahaya mesti dielakkan pada setiap masa.\n"
                    "Bawa semua lima suspek dan tiga bukti merentasi sungai dengan selamat.\n"
                    "Ini peluang terakhir anda. Keadilan bergantung kepada anda.",
                ],
            },
        }

    def t(self, key):
        return self.TR[self.lang].get(key, key)

    # ── Sound ─────────────────────────────────────────────────────────────

    def _init_sound(self):
        try:
            pygame.mixer.init()
            self._sounds = {}
            import os
            here = os.path.dirname(os.path.abspath(__file__))

            bg = os.path.join(here, "sounds", "bg_sound.mp3")
            if os.path.isfile(bg):
                pygame.mixer.music.load(bg)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)

            for key, fname in [("sail", "sail.wav"),
                                ("win",  "win.wav"),
                                ("lose", "lose.wav")]:
                path = os.path.join(here, "sounds", fname)
                if os.path.isfile(path):
                    self._sounds[key] = pygame.mixer.Sound(path)
        except Exception:
            self._sounds = {}

    def play_sfx(self, key):
        if not self.sound_on:
            return
        sfx = getattr(self, "_sounds", {}).get(key)
        if sfx:
            sfx.play()

    def _toggle_sound(self):
        self.sound_on = not self.sound_on
        try:
            if self.sound_on:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()
        except Exception:
            pass

    # ── Level loading ──────────────────────────────────────────────────────

    def load_level(self, num):
        self.level_num   = num
        self.level       = create_level(num, self.W, self.H)
        self.boat        = Boat(self.W, self.H)
        self.boat.capacity = 2 if num == 1 else (3 if num == 2 else 4)
        self.boat._update_size()
        self.timer       = self.level.time_limit
        self._ms_acc     = 0
        self.score       = self.level.base_score + self.level.time_limit * 5
        self.move_count  = 0
        self.selection_index = -1
        self.popup_entity    = None
        self.msg         = ""
        self.msg_timer   = 0
        self.open_page   = 0
        for entity in self.level.all_entities:
            entity.image = self.char_images.get(entity.name)
        self._place_entities()
        self.state = "OPENING"

    def restart_level(self):
        num = self.level_num
        self.level       = create_level(num, self.W, self.H)
        self.boat        = Boat(self.W, self.H)
        self.boat.capacity = 2 if num == 1 else (3 if num == 2 else 4)
        self.boat._update_size()
        self.timer       = self.level.time_limit
        self._ms_acc     = 0
        self.score       = self.level.base_score + self.level.time_limit * 5
        self.move_count  = 0
        self.selection_index = -1
        self.popup_entity    = None
        self.msg         = ""
        self.msg_timer   = 0
        for entity in self.level.all_entities:
            entity.image = self.char_images.get(entity.name)
        self._place_entities()
        self.state = "PLAYING"

    def _place_entities(self):
        entities = self.level.all_entities
        n        = max(len(entities), 1)
        BANK_W   = 215
        IMG_W    = 55
        IMG_H    = 70
        LABEL_H  = 18
        ENTITY_H = IMG_H + LABEL_H + 4

        earth_y  = self.H // 2 - 45
        avail    = self.H - earth_y - 8
        gap      = min(ENTITY_H + 4, avail // n)
        ex       = (BANK_W - IMG_W) // 2

        for i, e in enumerate(entities):
            e.x    = ex
            e.y    = earth_y + 6 + i * gap
            e.side = "left"
            e.selected = False
            e.update_rect()

    def _restack_banks(self):
        left  = [e for e in self.level.all_entities if e.side == "left"]
        right = [e for e in self.level.all_entities if e.side == "right"]

        BANK_W   = 215
        IMG_W    = 55
        IMG_H    = 70
        LABEL_H  = 18
        ENTITY_H = IMG_H + LABEL_H + 4

        earth_y  = self.H // 2 - 45
        n_max    = max(max(len(left), len(right)), 1)
        avail    = self.H - earth_y - 8
        gap      = min(ENTITY_H + 4, avail // n_max)

        left_x  = (BANK_W - IMG_W) // 2
        right_x = self.W - BANK_W + (BANK_W - IMG_W) // 2

        for i, e in enumerate(left):
            e.x = left_x;   e.y = earth_y + 6 + i * gap;  e.update_rect()
        for i, e in enumerate(right):
            e.x = right_x;  e.y = earth_y + 6 + i * gap;  e.update_rect()

    # ── Main loop hooks ───────────────────────────────────────────────────

    def update(self, dt_ms):
        if self.state == "PLAYING":
            self._ms_acc += dt_ms
            if self._ms_acc >= 1000:
                self._ms_acc -= 1000
                self.timer  -= 1
                if self.timer <= 0:
                    self.timer = 0
                    self._lose("Banjir menjadi terlalu berbahaya." if self.lang == "MY"
                               else "The flood became too dangerous.")

            arrived = self.boat.update()
            if arrived:
                self._on_arrival()

            if self.msg_timer > 0:
                self.msg_timer -= 1
            if self.popup_timer > 0:
                self.popup_timer -= 1
            else:
                self.popup_entity = None

            self.wave = (self.wave + 1) % 80

        if self.state == "OPENING":
            for drop in self._rain_drops:
                drop[1] += drop[2]
                if drop[1] > self.H + 20:
                    import random
                    drop[0] = random.randint(0, self.W)
                    drop[1] = random.randint(-40, 0)
                    drop[2] = random.uniform(1.5, 3.5)

        self.rain_seed = (self.rain_seed + 1) % 9999

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self._on_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._on_click(pygame.mouse.get_pos())

    # ── Key handling ──────────────────────────────────────────────────────

    def _on_key(self, key):
        s = self.state

        if s == "LEVEL_SELECT":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"

        elif s == "HELP_POPUP":
            self.state = "PLAYING"

        elif s == "INSTRUCTION":
            if key == pygame.K_RETURN:
                self.state = "PLAYING"
            elif key == pygame.K_ESCAPE:
                self.state = "PLAYING"
            else:
                self.state = "PLAYING"

        elif s == "OPENING":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._opening_advance()

        elif s == "PLAYING":
            if   key == pygame.K_p:      self.state = "PAUSED"
            elif key == pygame.K_r:      self.restart_level()
            elif key == pygame.K_ESCAPE: self.state = "MENU"
            elif key == pygame.K_a:      self._shift_selection(-1)
            elif key == pygame.K_d:      self._shift_selection(1)
            elif key == pygame.K_SPACE:  self._toggle_selected()
            elif key == pygame.K_RETURN:
                if not self.boat.moving:
                    self._sail()

        elif s == "PAUSED":
            if   key == pygame.K_p:      self.state = "PLAYING"
            elif key == pygame.K_r:      self.restart_level()
            elif key == pygame.K_ESCAPE: self.state = "LEVEL_SELECT"

        elif s in ("WIN", "LEVEL_CLEAR", "LOSE"):
            if key == pygame.K_RETURN:
                if s == "LEVEL_CLEAR":
                    self._advance_level()
                else:
                    self.state = "MENU"
            elif key == pygame.K_r and s == "LOSE":
                self.restart_level()

    def _opening_advance(self):
        pages = self.STORY_PAGES.get(self.level_num, {}).get(self.lang, [""])
        self.open_page += 1
        if self.open_page >= len(pages):
            self.state = "INSTRUCTION"

    # ── Selection helpers ─────────────────────────────────────────────────

    def _shift_selection(self, direction):
        entities = self.level.all_entities
        if 0 <= self.selection_index < len(entities):
            entities[self.selection_index].selected = False
        self.selection_index = (self.selection_index + direction) % len(entities)
        entities[self.selection_index].selected = True

    def _toggle_selected(self):
        if self.selection_index < 0:
            self._show_msg("Press A/D to select an entity first." if self.lang == "EN"
                           else "Tekan A/D untuk pilih entiti dahulu.")
            return
        entities = self.level.all_entities
        if self.selection_index >= len(entities):
            return
        self._interact(entities[self.selection_index])

    # ── Click handling ────────────────────────────────────────────────────

    def _on_click(self, pos):
        s = self.state

        if self._sound_btn_rect().collidepoint(pos):
            self._toggle_sound()
            return

        if self._lang_btn_rect().collidepoint(pos):
            self.lang = "MY" if self.lang == "EN" else "EN"
            return

        if   s == "MENU":          self._menu_click(pos)
        elif s == "HOW_TO_PLAY":   self.state = "MENU"
        elif s == "LEVEL_SELECT":  self._level_select_click(pos)
        elif s == "OPENING":       self._opening_click(pos)
        elif s == "INSTRUCTION":   self._instruction_click(pos)
        elif s == "HELP_POPUP":    self._help_popup_click(pos)
        elif s == "LEVEL_CLEAR":   self._level_clear_click(pos)
        elif s == "LOSE":          self._lose_click(pos)
        elif s == "PLAYING" and not self.boat.moving:
            self._game_click(pos)
        elif s == "PAUSED":        self._pause_click(pos)

    def _level_select_click(self, pos):
        cx     = self.W // 2
        card_w, card_h = 240, 300
        gap    = 60
        total_w = self.MAX_LEVELS * card_w + (self.MAX_LEVELS - 1) * gap
        start_x = cx - total_w // 2
        card_y  = (self.H - card_h) // 2

        for i in range(self.MAX_LEVELS):
            num  = i + 1
            rect = pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
            if rect.collidepoint(pos):
                if num <= self.unlocked_levels:
                    self.total_score = 0
                    self.load_level(num)
                return

        back_r = pygame.Rect(cx - 132, self.H - 80, 265, 52)
        if back_r.collidepoint(pos):
            self.state = "MENU"

    def _instruction_click(self, pos):
        cx  = self.W // 2
        cy  = self.H // 2
        pw  = min(780, self.W - 80)
        ph  = 460
        px  = cx - pw // 2
        py  = cy - ph // 2

        x_r     = pygame.Rect(px + pw - 44, py + 10, 34, 34)
        start_r = pygame.Rect(cx - 190, py + ph - 88, 380, 52)

        if x_r.collidepoint(pos) or start_r.collidepoint(pos):
            self.state = "PLAYING"

    def _opening_click(self, pos):
        back_r, next_r = self._opening_btn_rects()
        if next_r.collidepoint(pos):
            self._opening_advance()
        elif back_r.collidepoint(pos):
            if self.open_page > 0:
                self.open_page -= 1
            else:
                self.state = "LEVEL_SELECT"

    def _menu_click(self, pos):
        cx     = self.W // 2
        bw, bh = 265, 60
        y_start, gap = 310, 78
        btns = [
            self._start_game,
            lambda: setattr(self, "state", "HOW_TO_PLAY"),
            self._quit,
        ]
        for i, action in enumerate(btns):
            rect = pygame.Rect(cx - bw // 2, y_start + i * gap, bw, bh)
            if rect.collidepoint(pos):
                action()
                return

    def _start_game(self):
        self.total_score = 0
        self.state = "LEVEL_SELECT"

    def _advance_level(self):
        nxt = self.level_num + 1
        if nxt <= self.MAX_LEVELS:
            self.total_score += self.score
            self.unlocked_levels = max(self.unlocked_levels, nxt)
            self.load_level(nxt)
        else:
            self.total_score += self.score
            self.state = "WIN"

    def _level_clear_click(self, pos):
        cx = self.W // 2
        nxt_r  = pygame.Rect(cx - 200, self.H - 110, 400, 58)
        menu_r = pygame.Rect(cx - 130, self.H - 42,  260, 34)
        if nxt_r.collidepoint(pos):
            self._advance_level()
        elif menu_r.collidepoint(pos):
            self.state = "MENU"

    def _lose_click(self, pos):
        restart_r, menu_r = self._lose_btn_rects()
        if restart_r.collidepoint(pos):
            self.restart_level()
        elif menu_r.collidepoint(pos):
            self.state = "MENU"

    def _game_btn_rects(self):
        bw, bh    = 106, 30
        btn_gap   = 6
        lang_gap  = 10
        bx      = self.W - bw - 14
        help_y  = 79 + lang_gap
        pause_y = help_y + bh + btn_gap
        help_r  = pygame.Rect(bx, help_y,  bw, bh)
        pause_r = pygame.Rect(bx, pause_y, bw, bh)
        return help_r, pause_r

    def _help_popup_click(self, pos):
        self.state = "PLAYING"

    def _game_click(self, pos):
        help_r, pause_r = self._game_btn_rects()
        if help_r.collidepoint(pos):
            self.state = "HELP_POPUP"
            return
        if pause_r.collidepoint(pos):
            self.state = "PAUSED"
            return

        for entity in self.level.all_entities:
            if entity.is_clicked(pos):
                if entity.selected:
                    self.popup_entity = entity
                    self.popup_timer  = 200
                    entity.selected   = False
                    self.selection_index = -1
                else:
                    self._clear_selection()
                    entity.selected = True
                    self.selection_index = self.level.all_entities.index(entity)
                return

        if self.boat.rect.collidepoint(pos):
            self._sail()
            return

        self._clear_selection()

    def _pause_click(self, pos):
        rects = self._pause_btn_rects()
        actions = [
            lambda: setattr(self, "state", "PLAYING"),
            self.restart_level,
            lambda: setattr(self, "state", "LEVEL_SELECT"),
        ]
        for rect, action in zip(rects, actions):
            if rect.collidepoint(pos):
                action()
                return

    # ── Game logic ────────────────────────────────────────────────────────

    def _interact(self, entity):
        translated_name = self.ENTITY_NAMES.get(self.lang, {}).get(entity.name, entity.name)
        if entity.side == "boat":
            self.boat.unload(entity)
            entity.side = self.boat.side
            self._restack_banks()
            self._clear_selection()
            self._validate()
        elif entity.side == self.boat.side:
            if self.boat.load(entity):
                self._clear_selection()
                self._validate()
            else:
                cap = self.boat.capacity
                if cap >= 4:
                    self._show_msg("Bot penuh! (Detektif + 3 maks)" if self.lang == "MY"
                                   else "Boat is full! (Detective + 3 max)")
                elif cap >= 3:
                    self._show_msg("Bot penuh! (Detektif + 2 maks)" if self.lang == "MY"
                                   else "Boat is full! (Detective + 2 max)")
                else:
                    self._show_msg("Bot penuh! (Detektif + 1 maks)" if self.lang == "MY"
                                   else "Boat is full! (Detective + 1 max)")
        else:
            self._show_msg(f"{translated_name} berada di tebing seberang!" if self.lang == "MY"
                           else f"{entity.name} is on the other bank!")

    def _sail(self):
        if self.boat.moving:
            return
        ok = self.boat.move()
        if ok:
            self.move_count += 1
            self.score = max(0, self.score - 15)
            self._validate()
        else:
            self._show_msg("Detektif James mesti berada di bot!" if self.lang == "MY"
                           else "Detective James must be on the boat!")

    def _on_arrival(self):
        self._restack_banks()
        self._validate()
        if self.level.check_win():
            self.score += self.timer * 3
            self.state  = "LEVEL_CLEAR"

    def _validate(self):
        violated, msg = self.level.validate_banks(self.boat.side)
        if violated:
            self._lose(msg)

    def _lose(self, reason):
        translations = {
            "Butler threw the Knife into the river!":
                "Butler mencampak Pisau ke dalam sungai!",
            "Maid destroyed the Secret Letter!":
                "Pembantu Rumah memusnahkan Surat Rahsia!",
            "Nephew stole the Safe Key and escaped!":
                "Anak Saudara mencuri Kunci Peti Besi dan melarikan diri!",
            "The flood became too dangerous.":
                "Banjir menjadi terlalu berbahaya.",
        }
        if self.lang == "MY":
            reason = translations.get(reason, reason)
        self.msg   = reason
        self.state = "LOSE"

    def _clear_selection(self):
        for e in self.level.all_entities:
            e.selected = False
        self.selection_index = -1

    def _show_msg(self, text, frames=130):
        self.msg       = text
        self.msg_timer = frames

    @staticmethod
    def _quit():
        pygame.quit()
        sys.exit()

    # ── Rect helpers ──────────────────────────────────────────────────────

    def _lang_btn_rect(self):
        return pygame.Rect(self.W - 120, 13, 106, 30)

    def _sound_btn_rect(self):
        return pygame.Rect(self.W - 120, 49, 106, 30)

    def _opening_btn_rects(self):
        bw, bh = 230, 58
        y      = self.H - 120
        cx     = self.W // 2
        gap    = 28
        back_r = pygame.Rect(cx - bw - gap // 2, y, bw, bh)
        next_r = pygame.Rect(cx + gap // 2,       y, bw, bh)
        return back_r, next_r

    # ── Master draw ───────────────────────────────────────────────────────

    def draw(self):
        s = self.state
        if   s == "MENU":         self._draw_menu()
        elif s == "HOW_TO_PLAY":  self._draw_how()
        elif s == "LEVEL_SELECT": self._draw_level_select()
        elif s == "OPENING":      self._draw_opening()
        elif s == "INSTRUCTION":  self._draw_instruction()
        elif s == "PLAYING":      self._draw_game()
        elif s == "HELP_POPUP":
            self._draw_game()
            self._draw_help_popup()
        elif s == "PAUSED":
            self._draw_game()
            self._draw_pause_overlay()
        elif s == "LEVEL_CLEAR":  self._draw_level_clear()
        elif s == "WIN":          self._draw_win()
        elif s == "LOSE":         self._draw_lose()
        pygame.display.flip()

    # ══════════════════════════════════════════════════════════════════════
    # MENU
    # ══════════════════════════════════════════════════════════════════════

    def _draw_menu(self):
        if self.bg_menu:
            self.screen.blit(self.bg_menu, (0, 0))
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 110))
            self.screen.blit(ov, (0, 0))
        else:
            self.screen.fill(DARK_BG)
            self._rain()

        cx = self.W // 2

        line1 = self.fonts["big"].render("MURDER CROSSING", True, WHITE)
        line2 = self.fonts["big"].render("GAME",            True, WHITE)
        self.screen.blit(line1, (cx - line1.get_width() // 2, 90))
        self.screen.blit(line2, (cx - line2.get_width() // 2, 148))

        badge_text = self.fonts["small"].render("THE BLACKWOOD CASE", True, (20, 15, 10))
        bpad_x, bpad_y = 24, 8
        bw = badge_text.get_width()  + bpad_x * 2
        bh = badge_text.get_height() + bpad_y * 2
        badge_rect = pygame.Rect(cx - bw // 2, 218, bw, bh)
        pygame.draw.rect(self.screen, CREAM, badge_rect, border_radius=6)
        self.screen.blit(badge_text, (badge_rect.x + bpad_x, badge_rect.y + bpad_y))

        btn_w, btn_h = 265, 60
        y_start, gap = 310, 78
        labels = [
            self.t("start"),
            self.t("how"),
            self.t("exit"),
        ]
        mx, my = pygame.mouse.get_pos()
        for i, label in enumerate(labels):
            rect    = pygame.Rect(cx - btn_w // 2, y_start + i * gap, btn_w, btn_h)
            hovered = rect.collidepoint(mx, my)
            fill    = (255, 245, 220) if hovered else (240, 235, 215)
            alpha   = 240 if hovered else 200
            border  = (160, 140, 80) if hovered else (200, 195, 175)
            pygame.draw.rect(self.screen, (5, 3, 15),
                             pygame.Rect(rect.x+3, rect.y+3, btn_w, btn_h),
                             border_radius=30)
            btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_surf, (*fill, alpha), (0, 0, btn_w, btn_h),
                             border_radius=30)
            self.screen.blit(btn_surf, rect.topleft)
            pygame.draw.rect(self.screen, border, rect, 3 if hovered else 2,
                             border_radius=30)
            txt_col = (10, 8, 5) if hovered else (20, 15, 10)
            txt = self.fonts["medium"].render(label, True, txt_col)
            self.screen.blit(txt, (cx - txt.get_width() // 2,
                                   rect.y + (btn_h - txt.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # LEVEL SELECT
    # ══════════════════════════════════════════════════════════════════════

    def _draw_level_select(self):
        if self.bg_menu:
            self.screen.blit(self.bg_menu, (0, 0))
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 160))
            self.screen.blit(ov, (0, 0))
        else:
            self.screen.fill(DARK_BG)

        cx = self.W // 2

        ht = self.fonts["big"].render(self.t("sel_title"), True, WHITE)
        self.screen.blit(ht, (cx - ht.get_width() // 2, 55))

        LEVEL_META = {
            1: {
                "EN": ("The First Clue",    "Easy",   60,  ["Detective James", "Butler", "Maid", "Knife"]),
                "MY": ("Petanda Pertama",   "Mudah",  60,  ["Detective James", "Butler", "Maid", "Knife"]),
            },
            2: {
                "EN": ("Hidden Secrets",    "Medium", 90,  ["Detective James", "Butler", "Maid", "Doctor", "Knife", "Secret Letter"]),
                "MY": ("Rahsia Tersembunyi","Sederhana",90, ["Detective James", "Butler", "Maid", "Doctor", "Knife", "Secret Letter"]),
            },
            3: {
                "EN": ("The Truth Emerges", "Hard",   120, ["Detective James", "Butler", "Maid", "Doctor", "Nephew", "Knife", "Secret Letter", "Safe Key"]),
                "MY": ("Kebenaran Terbongkar","Susah",120, ["Detective James", "Butler", "Maid", "Doctor", "Nephew", "Knife", "Secret Letter", "Safe Key"]),
            },
        }
        diff_colors = {"Easy": GREEN, "Medium": GOLD, "Hard": RED,
                       "Mudah": GREEN, "Sederhana": GOLD, "Susah": RED}

        card_w, card_h = 240, 300
        gap     = 60
        total_w = self.MAX_LEVELS * card_w + (self.MAX_LEVELS - 1) * gap
        start_x = cx - total_w // 2
        card_y  = (self.H - card_h) // 2

        mx, my = pygame.mouse.get_pos()

        for i in range(self.MAX_LEVELS):
            num      = i + 1
            locked   = num > self.unlocked_levels
            meta     = LEVEL_META[num][self.lang]
            lv_name, diff, time_s, chars = meta
            card_x   = start_x + i * (card_w + gap)
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            hovered  = card_rect.collidepoint(mx, my) and not locked
            lift     = 7 if hovered else 0
            draw_r   = pygame.Rect(card_x, card_y - lift, card_w, card_h)

            pygame.draw.rect(self.screen, (5, 3, 15),
                             pygame.Rect(card_x + 6, card_y - lift + 6, card_w, card_h),
                             border_radius=14)

            body_col = (25, 18, 52) if not locked else (22, 20, 30)
            pygame.draw.rect(self.screen, body_col, draw_r, border_radius=14)
            border_col = (255, 210, 60) if hovered else ((80, 70, 30) if not locked else (50, 48, 55))
            pygame.draw.rect(self.screen, border_col, draw_r, 2, border_radius=14)

            badge_col = GOLD if not locked else GREY
            pygame.draw.circle(self.screen, badge_col, (card_x + card_w // 2, card_y - lift + 30), 24)
            nt = self.fonts["medium"].render(str(num), True, (15, 10, 5) if not locked else (80, 80, 80))
            self.screen.blit(nt, (card_x + card_w // 2 - nt.get_width() // 2,
                                  card_y - lift + 30 - nt.get_height() // 2))

            lv_lbl = self.fonts["tiny"].render(
                f"{'Level' if self.lang == 'EN' else 'Peringkat'} {num}", True, GREY)
            self.screen.blit(lv_lbl, (card_x + (card_w - lv_lbl.get_width()) // 2,
                                      card_y - lift + 58))

            col = WHITE if not locked else (80, 78, 85)
            nm  = self.fonts["small"].render(lv_name, True, col)
            if nm.get_width() > card_w - 16:
                words = lv_name.split()
                half  = len(words) // 2
                for li, part in enumerate([" ".join(words[:half]), " ".join(words[half:])]):
                    ps = self.fonts["small"].render(part, True, col)
                    self.screen.blit(ps, (card_x + (card_w - ps.get_width()) // 2,
                                         card_y - lift + 78 + li * 26))
            else:
                self.screen.blit(nm, (card_x + (card_w - nm.get_width()) // 2,
                                      card_y - lift + 78))

            dc = diff_colors.get(diff, GREY) if not locked else (70, 68, 75)
            dt = self.fonts["tiny"].render(diff, True, dc)
            self.screen.blit(dt, (card_x + (card_w - dt.get_width()) // 2,
                                  card_y - lift + 112))

            pygame.draw.line(self.screen, (55, 48, 80),
                             (card_x + 20, card_y - lift + 132),
                             (card_x + card_w - 20, card_y - lift + 132), 1)

            preview_chars = chars[:4]
            pw = 44
            total_pw = len(preview_chars) * pw + (len(preview_chars) - 1) * 4
            px_start = card_x + (card_w - total_pw) // 2
            py       = card_y - lift + 140

            for j, cname in enumerate(preview_chars):
                img = self.char_images.get(cname)
                px  = px_start + j * (pw + 4)
                if img:
                    small = pygame.transform.smoothscale(img, (pw, 54))
                    if locked:
                        grey_surf = small.copy()
                        grey_surf.fill((100, 100, 100, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        self.screen.blit(grey_surf, (px, py))
                    else:
                        self.screen.blit(small, (px, py))
                else:
                    col_c = GREY if locked else (100, 90, 160)
                    pygame.draw.circle(self.screen, col_c, (px + pw // 2, py + 27), 18)

            if len(chars) > 4:
                more = self.fonts["tiny"].render(f"+{len(chars)-4} more", True, GREY)
                self.screen.blit(more, (card_x + (card_w - more.get_width()) // 2,
                                        card_y - lift + 198))

            tc  = (140, 200, 255) if not locked else (60, 60, 70)
            tt  = self.fonts["tiny"].render(f"Time: {time_s}s", True, tc)
            self.screen.blit(tt, (card_x + (card_w - tt.get_width()) // 2,
                                  card_y - lift + 216))

            if locked:
                lk = self.fonts["medium"].render(self.t("locked"), True, (90, 88, 98))
                self.screen.blit(lk, (card_x + (card_w - lk.get_width()) // 2,
                                      card_y - lift + card_h - 48))
                lc_x = card_x + card_w // 2
                lc_y = card_y - lift + card_h - 72
                pygame.draw.rect(self.screen, (80, 78, 90),
                                 (lc_x - 14, lc_y, 28, 20), border_radius=4)
                pygame.draw.arc(self.screen, (80, 78, 90),
                                (lc_x - 10, lc_y - 14, 20, 20), 0, 3.14, 3)
            else:
                pb_r = pygame.Rect(card_x + 30, card_y - lift + card_h - 54, card_w - 60, 42)
                btn_col = (50, 185, 80) if hovered else (30, 120, 55)
                pygame.draw.rect(self.screen, btn_col, pb_r, border_radius=20)
                pygame.draw.rect(self.screen, GREEN, pb_r, 2, border_radius=20)
                pt = self.fonts["small"].render(self.t("play_btn"), True, WHITE)
                self.screen.blit(pt, (pb_r.x + (pb_r.w - pt.get_width()) // 2,
                                      pb_r.y + (pb_r.h - pt.get_height()) // 2))

        back_r = pygame.Rect(cx - 132, self.H - 80, 265, 52)
        bs = pygame.Surface((265, 52), pygame.SRCALPHA)
        pygame.draw.rect(bs, (240, 235, 215, 190), (0, 0, 265, 52), border_radius=28)
        self.screen.blit(bs, back_r.topleft)
        pygame.draw.rect(self.screen, (200, 195, 175), back_r, 2, border_radius=28)
        bt = self.fonts["medium"].render(self.t("back"), True, (20, 15, 10))
        self.screen.blit(bt, (back_r.x + (back_r.w - bt.get_width()) // 2,
                              back_r.y + (back_r.h - bt.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    def _instr_lines(self):
        data = {
            1: {
                "EN": [
                    "Please help Detective James transport all suspects and evidence",
                    "across the river to the nearest police station.",
                    "",
                    "The boat can only carry Detective James and ONE other person",
                    "or item at a time. Detective James must always be on the boat to sail.",
                    "",
                    "⚠  GAME OVER if the Butler is left alone with the Knife —",
                    "    he will throw it into the river!",
                ],
                "MY": [
                    "Sila bantu Detektif James membawa semua suspek dan bukti",
                    "merentasi sungai ke balai polis terdekat.",
                    "",
                    "Bot hanya boleh membawa Detektif James dan SATU orang lain",
                    "atau item pada satu masa. Detektif mesti sentiasa ada di bot.",
                    "",
                    "⚠  TAMAT PERMAINAN jika Butler ditinggalkan bersama Pisau —",
                    "    dia akan mencampakkannya ke dalam sungai!",
                ],
            },
            2: {
                "EN": [
                    "Please help Detective James transport all suspects and evidence",
                    "across the river. A secret letter has been discovered!",
                    "",
                    "The boat can carry Detective James and TWO others at a time.",
                    "",
                    "⚠  GAME OVER if the Butler is left alone with the Knife.",
                    "⚠  GAME OVER if the Maid is left alone with the Secret Letter —",
                    "    she will destroy the evidence!",
                    "",
                    "Detective James must always be on the boat to sail.",
                ],
                "MY": [
                    "Sila bantu Detektif James membawa semua suspek dan bukti",
                    "merentasi sungai. Satu surat rahsia telah ditemui!",
                    "",
                    "Bot boleh membawa Detektif James dan DUA orang lain pada satu masa.",
                    "",
                    "⚠  TAMAT jika Butler ditinggalkan bersama Pisau.",
                    "⚠  TAMAT jika Pembantu Rumah ditinggalkan bersama Surat Rahsia —",
                    "    dia akan memusnahkan bukti!",
                    "",
                    "Detektif mesti sentiasa ada di bot untuk belayar.",
                ],
            },
            3: {
                "EN": [
                    "The final case! Transport everyone across the river safely.",
                    "Three dangerous combinations must be avoided at all times.",
                    "",
                    "The boat can carry Detective James and THREE others at a time.",
                    "",
                    "⚠  GAME OVER if Butler is left alone with the Knife.",
                    "⚠  GAME OVER if Maid is left alone with the Secret Letter.",
                    "⚠  GAME OVER if Nephew is left alone with the Safe Key.",
                    "",
                    "Detective James must be on the boat to sail.",
                ],
                "MY": [
                    "Kes terakhir! Bawa semua orang merentasi sungai dengan selamat.",
                    "Tiga kombinasi berbahaya mesti dielakkan pada setiap masa.",
                    "",
                    "Bot boleh membawa Detektif James dan TIGA orang lain pada satu masa.",
                    "",
                    "⚠  TAMAT jika Butler ditinggalkan bersama Pisau.",
                    "⚠  TAMAT jika Pembantu Rumah ditinggalkan bersama Surat Rahsia.",
                    "⚠  TAMAT jika Anak Saudara ditinggalkan bersama Kunci Peti Besi.",
                    "",
                    "Detektif mesti ada di bot untuk belayar.",
                ],
            },
        }
        return data.get(self.level_num, {}).get(self.lang, [])

    # ══════════════════════════════════════════════════════════════════════
    # INSTRUCTION POPUP
    # ══════════════════════════════════════════════════════════════════════

    def _draw_instruction(self):
        self._draw_game()

        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.screen.blit(ov, (0, 0))

        cx = self.W // 2
        cy = self.H // 2
        pw = min(780, self.W - 60)
        ph = 460
        px = cx - pw // 2
        py = cy - ph // 2

        pygame.draw.rect(self.screen, (18, 14, 40), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.screen, GOLD,          (px, py, pw, ph), 2, border_radius=16)

        pygame.draw.rect(self.screen, (40, 28, 78), (px, py, pw, 52), border_radius=16)
        pygame.draw.rect(self.screen, (40, 28, 78), (px, py + 26, pw, 26))
        tt = self.fonts["medium"].render(self.t("instr_title"), True, WHITE)
        self.screen.blit(tt, (cx - tt.get_width() // 2, py + 11))

        x_r = pygame.Rect(px + pw - 44, py + 10, 34, 34)
        pygame.draw.rect(self.screen, RED, x_r, border_radius=6)
        xt  = self.fonts["small"].render("X", True, WHITE)
        self.screen.blit(xt, (x_r.x + (x_r.w - xt.get_width()) // 2,
                              x_r.y + (x_r.h - xt.get_height()) // 2))

        lines = self._instr_lines()
        text_y = py + 64
        icon_w = 18
        for line in lines:
            if line == "":
                text_y += 8
                continue
            is_warn = line.startswith("⚠")
            color = (255, 120, 80) if is_warn else \
                    GREY            if line.startswith("    ") else WHITE
            clean = line.strip()
            display = clean.lstrip("⚠").strip() if is_warn else clean
            surf  = self.fonts["tiny"].render(display, True, color)
            if is_warn and self.icon_over:
                scaled = pygame.transform.smoothscale(self.icon_over, (icon_w, icon_w))
                total_w = icon_w + 6 + surf.get_width()
                start_x = cx - total_w // 2
                self.screen.blit(scaled, (start_x, text_y + (surf.get_height() - icon_w) // 2))
                self.screen.blit(surf, (start_x + icon_w + 6, text_y))
            else:
                self.screen.blit(surf, (cx - surf.get_width() // 2, text_y))
            text_y += 26

        start_r = pygame.Rect(cx - 190, py + ph - 88, 380, 52)
        mx, my  = pygame.mouse.get_pos()
        hov_s   = start_r.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (35, 160, 70) if hov_s else (25, 130, 55),
                         start_r, border_radius=28)
        pygame.draw.rect(self.screen, (80, 220, 100) if hov_s else GREEN,
                         start_r, 3 if hov_s else 2, border_radius=28)
        st = self.fonts["medium"].render(self.t("instr_start"), True, WHITE)
        self.screen.blit(st, (cx - st.get_width() // 2,
                              start_r.y + (start_r.h - st.get_height()) // 2))

        cl_lbl = "Press any key or X to close" if self.lang == "EN" else "Tekan mana-mana kekunci atau X untuk tutup"
        cl = self.fonts["tiny"].render(cl_lbl, True, GREY)
        self.screen.blit(cl, (cx - cl.get_width() // 2, py + ph - 26))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # HOW TO PLAY
    # ══════════════════════════════════════════════════════════════════════

    def _draw_how(self):
        self.screen.fill((8, 5, 18))
        cx = self.W // 2

        title_lbl = "HOW TO PLAY" if self.lang == "EN" else "CARA BERMAIN"
        bw, bh = 500, 60
        bx = cx - bw // 2
        pygame.draw.rect(self.screen, (40, 28, 8), (bx, 18, bw, bh), border_radius=10)
        pygame.draw.rect(self.screen, GOLD,         (bx, 18, bw, bh), 2, border_radius=10)
        pygame.draw.rect(self.screen, (180, 140, 20),(bx+4, 22, bw-8, bh-8), 1, border_radius=7)
        tt = self.fonts["big"].render(title_lbl, True, GOLD)
        self.screen.blit(tt, (cx - tt.get_width() // 2, 18 + (bh - tt.get_height()) // 2))

        pad      = 30
        p_gap    = 18
        p_count  = 3
        p_w      = (self.W - pad * 2 - p_gap * (p_count - 1)) // p_count
        p_top    = 98
        p_h      = self.H - p_top - 90

        panels = [
            {
                "title_en": "OBJECTIVE",
                "title_my": "MATLAMAT",
                "color":    (20, 50, 20),
                "border":   (50, 180, 80),
                "hdr":      (30, 100, 40),
                "tcolor":   GREEN,
                "icon":     self.icon_objective,
            },
            {
                "title_en": "CONTROLS",
                "title_my": "KAWALAN",
                "color":    (18, 14, 45),
                "border":   GOLD,
                "hdr":      (40, 28, 78),
                "tcolor":   GOLD,
                "icon":     self.icon_control,
            },
            {
                "title_en": "RULES",
                "title_my": "PERATURAN",
                "color":    (28, 8, 8),
                "border":   RED,
                "hdr":      (65, 15, 15),
                "tcolor":   RED,
                "icon":     self.icon_rules,
            },
        ]

        content_en = [
            # OBJECTIVE
            [
                ("Transport ALL suspects", WHITE),
                ("and evidence from the", WHITE),
                ("Blackwood Mansion to", WHITE),
                ("the Police HQ safely.", WHITE),
                ("", WHITE),
                ("Rules only apply on the", (180, 220, 180)),
                ("LEFT bank — once at", (180, 220, 180)),
                ("Police HQ, all is safe.", (180, 220, 180)),
                ("", WHITE),
                ("3 levels of increasing", GOLD),
                ("difficulty await you.", GOLD),
            ],
            # CONTROLS
            [
                ("A / D", GOLD),
                ("Select entity", WHITE),
                ("", WHITE),
                ("SPACE", GOLD),
                ("Load / unload entity", WHITE),
                ("", WHITE),
                ("ENTER", GOLD),
                ("Sail the boat", WHITE),
                ("", WHITE),
                ("P", GOLD),
                ("Pause game", WHITE),
                ("R", GOLD),
                ("Restart level", WHITE),
                ("ESC", GOLD),
                ("Return to menu", WHITE),
                ("", WHITE),
                ("Click entity twice", (180, 200, 255)),
                ("to see their clue!", (180, 200, 255)),
            ],
            # RULES
            [
                ("Detective MUST be", WHITE),
                ("on the boat to sail.", WHITE),
                ("", WHITE),
                ("Boat capacity:", GOLD),
                ("Lv 1:  Detective + 1", WHITE),
                ("Lv 2:  Detective + 2", WHITE),
                ("Lv 3:  Detective + 3", WHITE),
                ("", WHITE),
                ("Forbidden pairs on LEFT", (255, 140, 100)),
                ("bank trigger GAME OVER", (255, 140, 100)),
                ("if left unsupervised.", (255, 140, 100)),
                ("", WHITE),
                ("Plan every move!", RED),
            ],
        ]

        content_my = [
            # OBJECTIVE
            [
                ("Bawa SEMUA suspek", WHITE),
                ("dan bukti dari Blackwood", WHITE),
                ("Mansion ke Balai Polis", WHITE),
                ("dengan selamat.", WHITE),
                ("", WHITE),
                ("Peraturan hanya berlaku", (180, 220, 180)),
                ("di tebing KIRI — sekali", (180, 220, 180)),
                ("di Balai Polis, selamat.", (180, 220, 180)),
                ("", WHITE),
                ("3 peringkat kesukaran", GOLD),
                ("menunggu anda!", GOLD),
            ],
            # CONTROLS
            [
                ("A / D", GOLD),
                ("Pilih entiti", WHITE),
                ("", WHITE),
                ("SPACE", GOLD),
                ("Naik / turun bot", WHITE),
                ("", WHITE),
                ("ENTER", GOLD),
                ("Belayar merentasi sungai", WHITE),
                ("", WHITE),
                ("P", GOLD),
                ("Jeda permainan", WHITE),
                ("R", GOLD),
                ("Mula semula peringkat", WHITE),
                ("ESC", GOLD),
                ("Kembali ke menu", WHITE),
                ("", WHITE),
                ("Klik entiti dua kali", (180, 200, 255)),
                ("untuk lihat petanda!", (180, 200, 255)),
            ],
            # RULES
            [
                ("Detektif MESTI berada", WHITE),
                ("di bot untuk belayar.", WHITE),
                ("", WHITE),
                ("Kapasiti bot:", GOLD),
                ("Lv 1:  Detektif + 1", WHITE),
                ("Lv 2:  Detektif + 2", WHITE),
                ("Lv 3:  Detektif + 3", WHITE),
                ("", WHITE),
                ("Pasangan larangan di tebing", (255, 140, 100)),
                ("KIRI menyebabkan TAMAT", (255, 140, 100)),
                ("jika ditinggalkan.", (255, 140, 100)),
                ("", WHITE),
                ("Rancang setiap langkah!", RED),
            ],
        ]

        content = content_en if self.lang == "EN" else content_my
        mx, my = pygame.mouse.get_pos()

        for pi, panel in enumerate(panels):
            px = pad + pi * (p_w + p_gap)
            pr = pygame.Rect(px, p_top, p_w, p_h)

            pygame.draw.rect(self.screen, (5, 3, 12),
                             pygame.Rect(px + 4, p_top + 4, p_w, p_h), border_radius=14)
            pygame.draw.rect(self.screen, panel["color"], pr, border_radius=14)
            pygame.draw.rect(self.screen, panel["border"], pr, 2, border_radius=14)

            pygame.draw.rect(self.screen, panel["hdr"],
                             (px, p_top, p_w, 48), border_radius=14)
            pygame.draw.rect(self.screen, panel["hdr"],
                             (px, p_top + 24, p_w, 24))
            title_key = "title_en" if self.lang == "EN" else "title_my"
            ht = self.fonts["small"].render(panel[title_key], True, panel["tcolor"])

            icon = panel.get("icon")
            if icon:
                gap_i    = 8
                total_w  = icon.get_width() + gap_i + ht.get_width()
                start_x  = px + (p_w - total_w) // 2
                icon_y   = p_top + (48 - icon.get_height()) // 2
                self.screen.blit(icon, (start_x, icon_y))
                self.screen.blit(ht,   (start_x + icon.get_width() + gap_i,
                                        p_top + (48 - ht.get_height()) // 2))
            else:
                self.screen.blit(ht, (px + (p_w - ht.get_width()) // 2,
                                      p_top + (48 - ht.get_height()) // 2))

            ly = p_top + 58
            for (text, color) in content[pi]:
                if text == "":
                    ly += 6
                    continue
                st = self.fonts["tiny"].render(text, True, color)
                self.screen.blit(st, (px + (p_w - st.get_width()) // 2, ly))
                ly += 22

        back_lbl = "Click anywhere to go back." if self.lang == "EN" \
                   else "Klik di mana-mana untuk kembali."
        bs = self.fonts["tiny"].render(back_lbl, True, (80, 80, 100))
        self.screen.blit(bs, (cx - bs.get_width() // 2, self.H - 32))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # OPENING / STORY SCREEN
    # ══════════════════════════════════════════════════════════════════════

    def _draw_opening(self):
        if self.bg_opening:
            self.screen.blit(self.bg_opening, (0, 0))
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            self.screen.blit(ov, (0, 0))
        else:
            self.screen.fill(OPENING_BG)

        rain_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for drop in self._rain_drops:
            x, y, speed, alpha = drop
            length = int(speed * 3)
            col = (140, 180, 240, 55)
            pygame.draw.line(rain_surf, col,
                             (int(x), int(y)),
                             (int(x) - 1, int(y) + length), 1)
        self.screen.blit(rain_surf, (0, 0))

        cx = self.W // 2

        lv_num  = self.level.level_number
        lv_names_my = {
            1: "Petanda Pertama",
            2: "Rahsia Tersembunyi",
            3: "Kebenaran Terbongkar",
        }
        lv_name = lv_names_my.get(lv_num, self.level.title.split("—")[-1].strip()) \
                  if self.lang == "MY" else self.level.title.split("—")[-1].strip()
        header  = f"{self.t('level_lbl')} {lv_num}: {lv_name}"
        t       = self.fonts["medium"].render(header, True, WHITE)
        self.screen.blit(t, (cx - t.get_width() // 2, 55))

        pages    = self.STORY_PAGES.get(self.level_num, {}).get(self.lang, [""])
        page_idx = min(self.open_page, len(pages) - 1)
        raw_text = pages[page_idx]

        max_chars_per_line = 72
        wrapped = self._wrap_text(raw_text, max_chars_per_line)

        box_x  = cx - 440
        box_y  = 110
        box_w  = 880
        btn_y  = self.H - 130
        avail_h = btn_y - box_y - 20
        line_h = min(34, max(22, avail_h // max(len(wrapped), 1)))
        box_h  = len(wrapped) * line_h + 16

        panel_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_s, (10, 8, 30, 0), (0, 0, box_w, box_h), border_radius=12)
        self.screen.blit(panel_s, (box_x, box_y))

        for i, line in enumerate(wrapped):
            rendered = self.fonts["small"].render(line, True, CREAM)
            self.screen.blit(rendered, (cx - rendered.get_width() // 2,
                                        box_y + 16 + i * line_h))

        is_last_page = (self.open_page >= len(pages) - 1)
        next_label   = ("Play Now" if self.lang == "EN" else "Main Sekarang") \
                       if is_last_page else self.t("next_btn")

        back_r, next_r = self._opening_btn_rects()
        mx, my = pygame.mouse.get_pos()
        for rect, label, is_next in ((back_r, self.t("back"), False),
                                     (next_r, next_label,     True)):
            hov      = rect.collidepoint(mx, my)
            if is_next and is_last_page:
                base_col = (80, 210, 120, 210)
                brd_col  = (50, 180, 80) if not hov else (80, 220, 100)
            else:
                base_col = (150, 230, 220, 210)
                brd_col  = (100, 200, 190) if not hov else (140, 230, 220)
            if hov:
                base_col = (base_col[0]+20, base_col[1]+20,
                            base_col[2]+20, base_col[3])
            btn_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(btn_surf, base_col, (0, 0, rect.w, rect.h),
                             border_radius=30)
            self.screen.blit(btn_surf, rect.topleft)
            pygame.draw.rect(self.screen, brd_col, rect,
                             3 if hov else 2, border_radius=30)
            txt = self.fonts["small"].render(label, True, (10, 10, 10))
            self.screen.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2,
                                   rect.y + (rect.h - txt.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    @staticmethod
    def _wrap_text(text, max_chars):
        result = []
        for paragraph in text.split("\n"):
            if not paragraph:
                result.append("")
                continue
            words  = paragraph.split()
            line   = ""
            for word in words:
                test = f"{line} {word}".strip()
                if len(test) <= max_chars:
                    line = test
                else:
                    if line:
                        result.append(line)
                    line = word
            if line:
                result.append(line)
        return result

    # ══════════════════════════════════════════════════════════════════════
    # GAME SCREEN
    # ══════════════════════════════════════════════════════════════════════

    def _draw_game(self):
        self.screen.fill(DARK_BG)

        MID = self.H // 2

        pygame.draw.rect(self.screen, (8, 4, 20),
                         (0, 0, self.W, MID - 50))

        pygame.draw.rect(self.screen, BANK_EARTH, (0, MID-45, 215, self.H))
        pygame.draw.rect(self.screen, BANK_GRASS, (0, MID-65, 215, 28))

        pygame.draw.rect(self.screen, BANK_EARTH, (self.W-215, MID-45, 215, self.H))
        pygame.draw.rect(self.screen, BANK_GRASS, (self.W-215, MID-65, 215, 28))

        river = pygame.Rect(215, MID-45, self.W-430, self.H - (MID-45))
        pygame.draw.rect(self.screen, RIVER_D, river)

        import random
        river_left = 225
        rw         = self.W - 430 - 70
        river_top  = MID - 45
        river_h    = self.H - river_top
        wave_w     = 70
        wave_h     = 18

        num_rows = 8
        rng      = random.Random(99)
        row_h    = river_h // num_rows

        for row in range(num_rows):
            start_x = rng.randint(0, rw)
            wx = river_left + (start_x + self.wave * 3) % rw
            wy = river_top + row * row_h + (row_h - wave_h) // 2
            pygame.draw.arc(self.screen, RIVER_L,
                            (wx, wy, wave_w, wave_h), 0, 3.14, 2)
            wx2 = river_left + (start_x + self.wave * 3 + rw // 2) % rw
            pygame.draw.arc(self.screen, RIVER_L,
                            (wx2, wy, wave_w, wave_h), 0, 3.14, 2)

        ml_txt = "BLACKWOOD MANSION" if self.lang == "EN" else "MANSION BLACKWOOD"
        pr_txt = "POLICE HQ"         if self.lang == "EN" else "IBU PEJABAT POLIS"
        ml = self.fonts["tiny"].render(ml_txt, True, (170, 140, 70))
        pr = self.fonts["tiny"].render(pr_txt, True, (170, 140, 70))
        self.screen.blit(ml, (5, MID - 90))
        self.screen.blit(pr, (self.W - pr.get_width() - 5, MID - 90))

        for e in self.level.all_entities:
            if e.side != "boat":
                self._draw_entity(e)

        self.boat.draw(self.screen, self.fonts["tiny"])

        for e in self.level.all_entities:
            if e.side == "boat":
                self._draw_entity(e)

        self._draw_hud()

        if self.popup_entity and self.popup_timer > 0:
            self._draw_popup(self.popup_entity)

        if self.msg_timer > 0:
            self._draw_msg_bar(self.msg)

        hint = self.fonts["tiny"].render(self.t("hint_sail"), True, (100, 100, 100))
        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 26))

        help_r, pause_r = self._game_btn_rects()
        mx, my = pygame.mouse.get_pos()
        btn_labels = [
            (help_r,  "HELP"  if self.lang == "EN" else "BANTUAN", TEAL),
            (pause_r, "PAUSE" if self.lang == "EN" else "JEDA",    (200, 180, 40)),
        ]
        for rect, label, col in btn_labels:
            hov      = rect.collidepoint(mx, my)
            fill_col = tuple(min(255, c + 40) for c in col) if hov else PANEL
            pygame.draw.rect(self.screen, fill_col, rect, border_radius=12)
            pygame.draw.rect(self.screen, col, rect,
                             3 if hov else 2, border_radius=12)
            lt = self.fonts["tiny"].render(label, True,
                                           (255,255,255) if hov else col)
            self.screen.blit(lt, (rect.x + (rect.w - lt.get_width()) // 2,
                                  rect.y + (rect.h - lt.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    def _draw_help_popup(self):
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        self.screen.blit(ov, (0, 0))

        cx = self.W // 2
        cy = self.H // 2
        pw = min(780, self.W - 60)
        ph = 460
        px = cx - pw // 2
        py = cy - ph // 2

        pygame.draw.rect(self.screen, (18, 14, 40), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.screen, GOLD,          (px, py, pw, ph), 2, border_radius=16)

        pygame.draw.rect(self.screen, (40, 28, 78), (px, py, pw, 52), border_radius=16)
        pygame.draw.rect(self.screen, (40, 28, 78), (px, py + 26, pw, 26))
        ht_lbl = "HELP" if self.lang == "EN" else "BANTUAN"
        ht = self.fonts["medium"].render(ht_lbl, True, WHITE)
        self.screen.blit(ht, (cx - ht.get_width() // 2, py + 11))

        x_r = pygame.Rect(px + pw - 44, py + 10, 34, 34)
        pygame.draw.rect(self.screen, RED, x_r, border_radius=6)
        xt  = self.fonts["small"].render("X", True, WHITE)
        self.screen.blit(xt, (x_r.x + (x_r.w - xt.get_width()) // 2,
                              x_r.y + (x_r.h - xt.get_height()) // 2))

        lines  = self._instr_lines()
        text_y = py + 64
        icon_w = 18
        for line in lines:
            if line == "":
                text_y += 8
                continue
            is_warn = line.startswith("⚠")
            color = (255, 120, 80) if is_warn else \
                    GREY            if line.startswith("    ") else WHITE
            clean = line.strip()
            display = clean.lstrip("⚠").strip() if is_warn else clean
            surf  = self.fonts["tiny"].render(display, True, color)
            if is_warn and self.icon_over:
                scaled = pygame.transform.smoothscale(self.icon_over, (icon_w, icon_w))
                total_w = icon_w + 6 + surf.get_width()
                start_x = cx - total_w // 2
                self.screen.blit(scaled, (start_x, text_y + (surf.get_height() - icon_w) // 2))
                self.screen.blit(surf, (start_x + icon_w + 6, text_y))
            else:
                self.screen.blit(surf, (cx - surf.get_width() // 2, text_y))
            text_y += 26

        close_r = pygame.Rect(cx - 130, py + ph - 68, 260, 46)
        mx, my  = pygame.mouse.get_pos()
        hov_c   = close_r.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (130, 40, 40) if hov_c else (100, 30, 30),
                         close_r, border_radius=24)
        pygame.draw.rect(self.screen, (220, 80, 80) if hov_c else RED,
                         close_r, 3 if hov_c else 2, border_radius=24)
        cl = self.fonts["small"].render("Close  [any key]" if self.lang == "EN"
                                        else "Tutup  [mana-mana kekunci]", True, WHITE)
        self.screen.blit(cl, (cx - cl.get_width() // 2,
                              close_r.y + (close_r.h - cl.get_height()) // 2))

        self._draw_lang_btn()

    def _draw_entity(self, entity):
        """Draw entity with translated name for current language."""
        translated = self.ENTITY_NAMES.get(self.lang, {}).get(entity.name, entity.name)
        original   = entity.name
        entity.name = translated
        entity.draw(self.screen, self.fonts["tiny"])
        entity.name = original

    def _draw_hud(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, self.W, 52))

        lv_word = "PERINGKAT" if self.lang == "MY" else "LEVEL"
        title_translations = {
            "Level 1 — The First Clue":    "Peringkat 1 — Petanda Pertama",
            "Level 2 — Hidden Secrets":    "Peringkat 2 — Rahsia Tersembunyi",
            "Level 3 — The Truth Emerges": "Peringkat 3 — Kebenaran Terbongkar",
        }
        lv_title = title_translations.get(self.level.title, self.level.title) \
                   if self.lang == "MY" else self.level.title
        lv = self.fonts["tiny"].render(
            f"{lv_word} {self.level_num}/{self.MAX_LEVELS}  ·  {lv_title}", True, GOLD)
        self.screen.blit(lv, (10, 16))

        tc = RED if self.timer <= 20 else WHITE
        ts = self.fonts["small"].render(f"{self.t('timer')}: {self.timer}s", True, tc)
        self.screen.blit(ts, (self.W // 2 - ts.get_width() // 2, 10))

        sc = self.fonts["tiny"].render(
            f"{self.t('score')}: {self.score}   {self.t('moves')}: {self.move_count}",
            True, WHITE)
        self.screen.blit(sc, (self.W - sc.get_width() - 170, 16))

    def _draw_popup(self, entity):
        pw, ph = 300, 95
        px = min(entity.x + entity.width + 8, self.W - pw - 8)
        py = max(entity.y, 55)
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=8)
        pygame.draw.rect(self.screen, GOLD,  panel, 2, border_radius=8)
        for i, line in enumerate(entity.description.split("\n")):
            s = self.fonts["tiny"].render(line, True, WHITE)
            self.screen.blit(s, (px + 10, py + 10 + i * 26))

    def _draw_msg_bar(self, text):
        bar = pygame.Rect(0, self.H - 50, self.W, 26)
        pygame.draw.rect(self.screen, DARK_RED, bar)
        s = self.fonts["tiny"].render(text, True, WHITE)
        self.screen.blit(s, (self.W // 2 - s.get_width() // 2, self.H - 47))

    # ══════════════════════════════════════════════════════════════════════
    # PAUSE
    # ══════════════════════════════════════════════════════════════════════

    def _pause_btn_rects(self):
        cx   = self.W // 2
        bw, bh = 300, 52
        gap  = 14
        base = self.H // 2 - 65
        return [pygame.Rect(cx - bw // 2, base + i * (bh + gap), bw, bh)
                for i in range(3)]

    def _draw_pause_overlay(self):
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        self.screen.blit(ov, (0, 0))

        cx  = self.W // 2
        pw, ph = 420, 360
        px  = cx - pw // 2
        py  = self.H // 2 - ph // 2

        pygame.draw.rect(self.screen, (18, 14, 40), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.screen, GOLD,          (px, py, pw, ph), 2, border_radius=16)

        pygame.draw.rect(self.screen, (40, 28, 78), (px, py, pw, 52), border_radius=16)
        pygame.draw.rect(self.screen, (40, 28, 78), (px, py + 26, pw, 26))
        pause_lbl = "PAUSED" if self.lang == "EN" else "DIJEDA"
        pt = self.fonts["medium"].render(pause_lbl, True, GOLD)
        self.screen.blit(pt, (cx - pt.get_width() // 2, py + 11))

        title_translations = {
            "Level 1 — The First Clue":    "Peringkat 1 — Petanda Pertama",
            "Level 2 — Hidden Secrets":    "Peringkat 2 — Rahsia Tersembunyi",
            "Level 3 — The Truth Emerges": "Peringkat 3 — Kebenaran Terbongkar",
        }
        lv_title = title_translations.get(self.level.title, self.level.title) \
                   if self.lang == "MY" else self.level.title

        line1 = self.fonts["tiny"].render(lv_title, True, GREY)
        line2 = self.fonts["tiny"].render(
            f"{self.t('timer')}: {self.timer}s   •   {self.t('score')}: {self.score}",
            True, GREY)
        self.screen.blit(line1, (cx - line1.get_width() // 2, py + 58))
        self.screen.blit(line2, (cx - line2.get_width() // 2, py + 76))

        resume_lbl = "RESUME"  if self.lang == "EN" else "TERUSKAN"
        replay_lbl = "REPLAY"  if self.lang == "EN" else "ULANG"
        back_lbl   = "BACK"    if self.lang == "EN" else "KEMBALI"

        btn_data = [
            (resume_lbl, GREEN,          (20, 100, 45)),
            (replay_lbl, (220, 160, 40), (90, 65, 15)),
            (back_lbl,   (130, 100, 200),(50, 38, 90)),
        ]

        rects = self._pause_btn_rects()
        mx, my = pygame.mouse.get_pos()
        for rect, (label, border_col, fill_col) in zip(rects, btn_data):
            hov      = rect.collidepoint(mx, my)
            draw_col = tuple(min(255, c + 35) for c in fill_col) if hov else fill_col
            brd      = tuple(min(255, c + 40) for c in border_col) if hov else border_col
            pygame.draw.rect(self.screen, draw_col, rect, border_radius=26)
            pygame.draw.rect(self.screen, brd, rect,
                             3 if hov else 2, border_radius=26)
            s = self.fonts["small"].render(label, True, WHITE)
            self.screen.blit(s, (cx - s.get_width() // 2,
                                 rect.y + (rect.h - s.get_height()) // 2))

        hint = self.fonts["tiny"].render(
            "[P] Resume  [R] Replay  [ESC] Back" if self.lang == "EN"
            else "[P] Teruskan  [R] Ulang  [ESC] Kembali",
            True, (70, 70, 70))
        self.screen.blit(hint, (cx - hint.get_width() // 2, py + ph - 22))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # LEVEL CLEAR
    # ══════════════════════════════════════════════════════════════════════

    def _draw_level_clear(self):
        self.screen.fill(DARK_BG)
        cx = self.W // 2

        banner_lbl = "LEVEL CLEAR!" if self.lang == "EN" else "PERINGKAT SELESAI!"
        banner = self.fonts["big"].render(banner_lbl, True, GOLD)
        self.screen.blit(banner, (cx - banner.get_width() // 2, 38))

        title_translations = {
            "Level 1 — The First Clue":    "Peringkat 1 — Petanda Pertama",
            "Level 2 — Hidden Secrets":    "Peringkat 2 — Rahsia Tersembunyi",
            "Level 3 — The Truth Emerges": "Peringkat 3 — Kebenaran Terbongkar",
        }
        lv_title = title_translations.get(self.level.title, self.level.title) \
                   if self.lang == "MY" else self.level.title
        sub = self.fonts["small"].render(lv_title, True, (180, 160, 80))
        self.screen.blit(sub, (cx - sub.get_width() // 2, 102))

        panel_w, panel_h = 480, 220
        panel_x = cx - panel_w // 2
        panel_y = 145
        panel_r = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, PANEL, panel_r, border_radius=14)
        pygame.draw.rect(self.screen, GOLD,  panel_r, 2, border_radius=14)

        score_label  = "SCORE"      if self.lang == "EN" else "MARKAH"
        moves_label  = "MOVES"      if self.lang == "EN" else "LANGKAH"
        time_label   = "TIME LEFT"  if self.lang == "EN" else "MASA TINGGAL"
        bonus_label  = "TIME BONUS" if self.lang == "EN" else "BONUS MASA"
        total_label  = "TOTAL"      if self.lang == "EN" else "JUMLAH"

        time_bonus   = self.timer * 3
        base_score   = self.score - time_bonus

        rows = [
            (score_label,  f"{base_score}",   WHITE),
            (moves_label,  f"{self.move_count}", WHITE),
            (time_label,   f"{self.timer}s",  WHITE),
            (bonus_label,  f"+{time_bonus}",  GREEN),
            (total_label,  f"{self.score}",   GOLD),
        ]

        row_h = panel_h // (len(rows) + 1)
        for i, (lbl, val, col) in enumerate(rows):
            y = panel_y + (i + 1) * row_h - 14
            if i == len(rows) - 1:
                pygame.draw.line(self.screen, (60, 50, 90),
                                 (panel_x + 20, y - 6),
                                 (panel_x + panel_w - 20, y - 6), 1)
            lt = self.fonts["small"].render(lbl, True, GREY)
            vt = self.fonts["small"].render(val, True, col)
            self.screen.blit(lt, (panel_x + 24,              y))
            self.screen.blit(vt, (panel_x + panel_w - 24 - vt.get_width(), y))

        story_y = panel_y + panel_h + 18
        hint_hdr = "CASE NOTE" if self.lang == "EN" else "NOTA KES"
        hdr = self.fonts["tiny"].render(f"— {hint_hdr} —", True, (120, 100, 50))
        self.screen.blit(hdr, (cx - hdr.get_width() // 2, story_y))
        story_y += 22

        ending_lines_my = {
            1: [
                "Pisau telah dijamin.",
                "Butler kelihatan gugup.",
                "Saksi baru tampil ke hadapan...",
            ],
            2: [
                "Surat mendedahkan pertikaian pusaka.",
                "Encik Blackwood merancang membuang",
                "seseorang dari wasiatnya.",
                "Senarai suspek bertambah...",
            ],
            3: [
                "IBU PEJABAT POLIS",
                "Semua suspek telah disoal siasat.",
                "DR. WILLIAM CARTER",
                "KES SELESAI.",
            ],
        }
        lines_to_show = self.level.ending_lines
        if self.lang == "MY":
            lines_to_show = ending_lines_my.get(self.level_num, self.level.ending_lines)

        shown = 0
        for line in lines_to_show:
            if shown >= 4:
                break
            if not line:
                continue
            color = RED  if "DR. WILLIAM" in line or "CASE CLOSED" in line or "KES SELESAI" in line else \
                    GOLD if (line.isupper() and line) else WHITE
            s = self.fonts["small"].render(line, True, color)
            self.screen.blit(s, (cx - s.get_width() // 2, story_y))
            story_y += 26
            shown += 1

        is_last = self.level_num >= self.MAX_LEVELS
        if is_last:
            btn_label = "See Results  [Enter]" if self.lang == "EN" else "Lihat Keputusan  [Enter]"
            btn_col   = GOLD
        else:
            btn_label = f"Next: Level {self.level_num + 1}  [Enter]" if self.lang == "EN" \
                        else f"Seterusnya: Peringkat {self.level_num + 1}  [Enter]"
            btn_col   = GREEN

        nxt_r = pygame.Rect(cx - 220, self.H - 110, 440, 58)
        mx, my = pygame.mouse.get_pos()
        hov_n  = nxt_r.collidepoint(mx, my)
        nxt_fill = (40, 160, 70) if hov_n else PANEL
        pygame.draw.rect(self.screen, nxt_fill, nxt_r, border_radius=30)
        pygame.draw.rect(self.screen, btn_col,  nxt_r,
                         3 if hov_n else 2, border_radius=30)
        nt = self.fonts["small"].render(btn_label, True, WHITE if hov_n else btn_col)
        self.screen.blit(nt, (cx - nt.get_width() // 2,
                              nxt_r.y + (nxt_r.h - nt.get_height()) // 2))

        menu_lbl = "Back to Menu" if self.lang == "EN" else "Kembali ke Menu"
        menu_r   = pygame.Rect(cx - 130, self.H - 42, 260, 34)
        mt = self.fonts["tiny"].render(menu_lbl, True, GREY)
        self.screen.blit(mt, (cx - mt.get_width() // 2, self.H - 38))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # WIN
    # ══════════════════════════════════════════════════════════════════════

    def _draw_win(self):
        cx = self.W // 2

        self.screen.fill((8, 5, 18))

        vign = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for r in range(max(self.W, self.H), 0, -6):
            alpha = max(0, min(60, int((1 - r / max(self.W, self.H)) * 80)))
            pygame.draw.circle(vign, (0, 0, 0, alpha), (cx, self.H // 2), r)
        self.screen.blit(vign, (0, 0))

        import random
        rng = random.Random(self.rain_seed // 4)
        for _ in range(18):
            px = rng.randint(30, self.W - 30)
            py = rng.randint(20, self.H - 20)
            pr = rng.randint(1, 3)
            pa = rng.randint(60, 180)
            sp = pygame.Surface((pr * 2 + 2, pr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(sp, (255, 210, 60, pa), (pr + 1, pr + 1), pr)
            self.screen.blit(sp, (px - pr, py - pr))

        banner_w, banner_h = 640, 72
        banner_x = cx - banner_w // 2
        banner_y = 22

        pygame.draw.rect(self.screen, (60, 40, 8),
                         (banner_x, banner_y, banner_w, banner_h), border_radius=10)
        pygame.draw.rect(self.screen, GOLD,
                         (banner_x, banner_y, banner_w, banner_h), 3, border_radius=10)
        pygame.draw.rect(self.screen, (200, 160, 30),
                         (banner_x + 5, banner_y + 5, banner_w - 10, banner_h - 10),
                         1, border_radius=7)

        win_lbl = self.t("win_t")
        wt = self.fonts["big"].render(win_lbl, True, GOLD)
        self.screen.blit(wt, (cx - wt.get_width() // 2, banner_y + (banner_h - wt.get_height()) // 2))

        rule_y = banner_y + banner_h + 16
        pygame.draw.line(self.screen, (80, 60, 15), (80, rule_y), (self.W - 80, rule_y), 1)
        diamond_pts = [(cx, rule_y - 5), (cx + 6, rule_y), (cx, rule_y + 5), (cx - 6, rule_y)]
        pygame.draw.polygon(self.screen, GOLD, diamond_pts)

        col_gap   = 40
        col_w     = (self.W - 160 - col_gap) // 2
        left_x    = 80
        right_x   = 80 + col_w + col_gap
        content_y = rule_y + 22

        lp_h = 380
        lp_r = pygame.Rect(left_x, content_y, col_w, lp_h)
        pygame.draw.rect(self.screen, (14, 10, 32), lp_r, border_radius=12)
        pygame.draw.rect(self.screen, (60, 45, 12), lp_r, 2, border_radius=12)

        pygame.draw.rect(self.screen, (40, 28, 8),
                         (left_x, content_y, col_w, 36), border_radius=12)
        pygame.draw.rect(self.screen, (40, 28, 8),
                         (left_x, content_y + 18, col_w, 18))
        hdr_lbl = "CASE SUMMARY" if self.lang == "EN" else "RINGKASAN KES"
        hs = self.fonts["tiny"].render(hdr_lbl, True, GOLD)
        self.screen.blit(hs, (left_x + (col_w - hs.get_width()) // 2, content_y + 8))

        summary_lines_en = [
            ("✓", "All suspects transported safely"),
            ("✓", "All evidence preserved"),
            ("✓", "Secret Letter decoded"),
            ("✓", "Murder weapon secured"),
            ("✓", "Killer identified"),
        ]
        summary_lines_my = [
            ("✓", "Semua suspek dibawa selamat"),
            ("✓", "Semua bukti dipelihara"),
            ("✓", "Surat Rahsia didedahkan"),
            ("✓", "Senjata bunuh dijamin"),
            ("✓", "Pembunuh dikenalpasti"),
        ]
        summary = summary_lines_en if self.lang == "EN" else summary_lines_my
        for i, (tick, txt) in enumerate(summary):
            ty = content_y + 46 + i * 44
            if self.icon_checkmark:
                self.screen.blit(self.icon_checkmark,
                                 (left_x + 8, ty + 12 - 14))
            else:
                pygame.draw.circle(self.screen, (30, 150, 60), (left_x + 22, ty + 12), 11)
                tk = self.fonts["tiny"].render(tick, True, WHITE)
                self.screen.blit(tk, (left_x + 22 - tk.get_width() // 2,
                                      ty + 12 - tk.get_height() // 2))
            ts2 = self.fonts["tiny"].render(txt, True, (210, 210, 210))
            self.screen.blit(ts2, (left_x + 42, ty + 4))
            if i < len(summary) - 1:
                pygame.draw.line(self.screen, (35, 28, 55),
                                 (left_x + 12, ty + 36),
                                 (left_x + col_w - 12, ty + 36), 1)

        rp_h = 380
        rp_r = pygame.Rect(right_x, content_y, col_w, rp_h)
        pygame.draw.rect(self.screen, (20, 8, 8), rp_r, border_radius=12)
        pygame.draw.rect(self.screen, (120, 30, 30), rp_r, 2, border_radius=12)

        pygame.draw.rect(self.screen, (60, 15, 15),
                         (right_x, content_y, col_w, 36), border_radius=12)
        pygame.draw.rect(self.screen, (60, 15, 15),
                         (right_x, content_y + 18, col_w, 18))
        rev_lbl = "CULPRIT IDENTIFIED" if self.lang == "EN" else "PESALAH DIKENALPASTI"
        rs = self.fonts["tiny"].render(rev_lbl, True, RED)
        self.screen.blit(rs, (right_x + (col_w - rs.get_width()) // 2, content_y + 8))

        name_lbl = "DR. WILLIAM CARTER"
        nl = self.fonts["medium"].render(name_lbl, True, RED)
        self.screen.blit(nl, (right_x + (col_w - nl.get_width()) // 2, content_y + 44))

        pygame.draw.line(self.screen, (80, 25, 25),
                         (right_x + 20, content_y + 78),
                         (right_x + col_w - 20, content_y + 78), 1)

        motive_en = [
            "Motive: Dr. Carter falsified patient",
            "records for years to collect illegal",
            "insurance payments. Blackwood",
            "discovered the fraud and threatened",
            "to expose him — Carter had to silence him.",
        ]
        motive_my = [
            "Motif: Dr. Carter memalsukan rekod",
            "pesakit bertahun-tahun untuk kutip",
            "bayaran insurans haram. Blackwood",
            "tahu penipuan ini dan mengancam",
            "mendedahkannya — Carter terpaksa diam.",
        ]
        method_en = [
            "Method: Carter poisoned Blackwood's",
            "evening tea, then planted the Knife",
            "to stage it as a robbery gone wrong.",
        ]
        method_my = [
            "Cara: Carter meracun teh malam",
            "Blackwood, lalu letak Pisau untuk",
            "menjadikannya seperti rompakan.",
        ]

        detail_lines = (motive_en + [""] + method_en) if self.lang == "EN" \
                       else (motive_my + [""] + method_my)

        text_start_y = content_y + 88
        for i, m in enumerate(detail_lines):
            if not m:
                text_start_y += 6
                continue
            ms = self.fonts["tiny"].render(m, True, (220, 140, 140))
            self.screen.blit(ms, (right_x + (col_w - ms.get_width()) // 2, text_start_y))
            text_start_y += 20

        stamp_y = content_y + rp_h - 72
        if self.icon_guilty:
            rotated = pygame.transform.rotate(self.icon_guilty, -8)
            stamp_x = right_x + (col_w - rotated.get_width()) // 2
            self.screen.blit(rotated, (stamp_x, stamp_y))
        else:
            stamp_surf = pygame.Surface((120, 44), pygame.SRCALPHA)
            pygame.draw.rect(stamp_surf, (180, 30, 30, 80),  (0, 0, 120, 44), border_radius=6)
            pygame.draw.rect(stamp_surf, (200, 40, 40, 180), (0, 0, 120, 44), 3, border_radius=6)
            rotated = pygame.transform.rotate(stamp_surf, -8)
            self.screen.blit(rotated,
                             (right_x + (col_w - rotated.get_width()) // 2, stamp_y))

        bar_y = content_y + 380 + 16
        pygame.draw.rect(self.screen, (18, 14, 40),
                         (80, bar_y, self.W - 160, 70), border_radius=10)
        pygame.draw.rect(self.screen, GOLD,
                         (80, bar_y, self.W - 160, 70), 2, border_radius=10)

        score_lbl = f"TOTAL {'SCORE' if self.lang == 'EN' else 'MARKAH'} :"
        sl = self.fonts["small"].render(score_lbl, True, GREY)
        sv = self.fonts["big"].render(str(self.total_score), True, GOLD)
        total_w = sl.get_width() + 16 + sv.get_width()
        sx = cx - total_w // 2
        sy = bar_y + (70 - sl.get_height()) // 2 + 4
        self.screen.blit(sl, (sx, sy + 6))
        self.screen.blit(sv, (sx + sl.get_width() + 16, bar_y + (70 - sv.get_height()) // 2))

        menu_r = pygame.Rect(cx - 180, bar_y + 82, 360, 52)
        mx, my = pygame.mouse.get_pos()
        hov    = menu_r.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (35, 25, 70) if hov else (20, 14, 45),
                         menu_r, border_radius=28)
        pygame.draw.rect(self.screen, (150, 120, 255) if hov else (100, 80, 200),
                         menu_r, 3 if hov else 2, border_radius=28)
        end_lbl = self.t("end")
        et = self.fonts["medium"].render(end_lbl, True, WHITE)
        self.screen.blit(et, (cx - et.get_width() // 2,
                              menu_r.y + (menu_r.h - et.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    # ══════════════════════════════════════════════════════════════════════
    # LOSE
    # ══════════════════════════════════════════════════════════════════════

    def _draw_lose(self):
        self.screen.fill((18, 4, 4))
        cx = self.W // 2

        if self.icon_over:
            icon_x = cx - self.icon_over.get_width() // 2
            icon_y = 52
            self.screen.blit(self.icon_over, (icon_x, icon_y))
            title_y = icon_y + self.icon_over.get_height() + 14
        else:
            title_y = 140

        t = self.fonts["big"].render(self.t("lose_t"), True, RED)
        self.screen.blit(t, (cx - t.get_width() // 2, title_y))

        r = self.fonts["medium"].render(self.msg, True, WHITE)
        self.screen.blit(r, (cx - r.get_width() // 2, title_y + 80))

        fl = self.fonts["small"].render(
            "The killer escapes into the night..." if self.lang == "EN"
            else "Pembunuh melarikan diri ke dalam malam...", True, GREY)
        self.screen.blit(fl, (cx - fl.get_width() // 2, title_y + 140))

        restart_r, menu_r = self._lose_btn_rects()

        restart_lbl = "RESTART  [R]"  if self.lang == "EN" else "MULA SEMULA  [R]"
        menu_lbl    = "MENU  [ESC]"   if self.lang == "EN" else "MENU  [ESC]"

        mx, my = pygame.mouse.get_pos()
        for rect, label, col in [
            (restart_r, restart_lbl, WHITE),
            (menu_r,    menu_lbl,    (200, 80, 80)),
        ]:
            hov      = rect.collidepoint(mx, my)
            fill_col = (60, 20, 20) if hov else (40, 10, 10)
            pygame.draw.rect(self.screen, fill_col, rect, border_radius=28)
            pygame.draw.rect(self.screen, col, rect,
                             3 if hov else 2, border_radius=28)
            s = self.fonts["medium"].render(label, True, WHITE)
            self.screen.blit(s, (cx - s.get_width() // 2,
                                 rect.y + (rect.h - s.get_height()) // 2))

        self._draw_sound_btn()
        self._draw_lang_btn()

    def _lose_btn_rects(self):
        cx   = self.W // 2
        bw, bh = 320, 56
        gap  = 20
        # FIX: use dynamic y based on icon height so buttons don't clip off-screen
        if self.icon_over:
            base_y = 52 + self.icon_over.get_height() + 14 + 80 + 140
        else:
            base_y = 450
        restart_r = pygame.Rect(cx - bw // 2, base_y,         bw, bh)
        menu_r    = pygame.Rect(cx - bw // 2, base_y + bh + gap, bw, bh)
        return restart_r, menu_r

    # ══════════════════════════════════════════════════════════════════════
    # SHARED HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _draw_btn(self, rect, label, font,
                  normal_fill, normal_border, normal_text,
                  hover_fill,  hover_border,  hover_text,
                  radius=28):
        mx, my   = pygame.mouse.get_pos()
        hovered  = rect.collidepoint(mx, my)
        fill     = hover_fill   if hovered else normal_fill
        border   = hover_border if hovered else normal_border
        text_col = hover_text   if hovered else normal_text

        if hovered:
            expand = 3
            draw_r = pygame.Rect(rect.x - expand, rect.y - expand,
                                 rect.w + expand*2, rect.h + expand*2)
        else:
            draw_r = rect

        shadow_r = pygame.Rect(draw_r.x + 3, draw_r.y + 3, draw_r.w, draw_r.h)
        pygame.draw.rect(self.screen, (5, 3, 15), shadow_r, border_radius=radius)

        pygame.draw.rect(self.screen, fill,   draw_r, border_radius=radius)
        pygame.draw.rect(self.screen, border, draw_r, 2 if not hovered else 3,
                         border_radius=radius)

        s = font.render(label, True, text_col)
        self.screen.blit(s, (draw_r.x + (draw_r.w - s.get_width())  // 2,
                             draw_r.y + (draw_r.h - s.get_height()) // 2))

    def _draw_lang_btn(self):
        rect   = self._lang_btn_rect()
        mx, my = pygame.mouse.get_pos()
        hov    = rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (0, 0, 0),
                         pygame.Rect(rect.x+2, rect.y+2, rect.w, rect.h), border_radius=8)
        fill = (35, 190, 175) if hov else (20, 155, 140)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE if hov else (160, 230, 225),
                         rect, 2, border_radius=8)
        s = self.fonts["tiny"].render(self.t("lang_lbl"), True, WHITE)
        self.screen.blit(s, (rect.x + (rect.w - s.get_width()) // 2,
                             rect.y + (rect.h - s.get_height()) // 2))

    def _draw_sound_btn(self):
        """Draw the sound toggle button. Self-contained — no helper needed."""
        rect   = self._sound_btn_rect()
        mx, my = pygame.mouse.get_pos()
        hov    = rect.collidepoint(mx, my)
        on     = self.sound_on
        pygame.draw.rect(self.screen, (0, 0, 0),
                         pygame.Rect(rect.x+2, rect.y+2, rect.w, rect.h), border_radius=8)
        fill = (35, 190, 175) if (hov and on) else \
               (80, 80, 80)   if hov else \
               (20, 155, 140) if on else (55, 55, 55)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen,
                         WHITE if hov else ((160, 230, 225) if on else (100, 100, 100)),
                         rect, 2, border_radius=8)
        icon = "SOUND ON" if on else "SOUND OFF"
        s = self.fonts["tiny"].render(icon, True, WHITE if on else (180, 180, 180))
        self.screen.blit(s, (rect.x + (rect.w - s.get_width()) // 2,
                             rect.y + (rect.h - s.get_height()) // 2))

    def _rain(self):
        import random
        rng = random.Random(self.rain_seed)
        for _ in range(55):
            x = rng.randint(0, self.W)
            y = rng.randint(0, self.H)
            pygame.draw.line(self.screen, (60, 85, 145),
                             (x, y), (x + rng.randint(-2, 2), y + rng.randint(12, 22)), 1)