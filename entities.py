import pygame


# Shared helper ─────────────────────────────────────────────────────────────

def _draw_name(screen, font, name, cx, y, selected=False):
    """Draw a centred name label below a sprite. White normally, gold when selected."""
    color = (255, 210, 40) if selected else (240, 240, 240)
    # Split long names onto two lines
    parts = name.split()
    if len(parts) <= 2:
        lines = [name]
    else:
        mid   = (len(parts) + 1) // 2
        lines = [" ".join(parts[:mid]), " ".join(parts[mid:])]
    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        screen.blit(surf, (cx - surf.get_width() // 2, y + i * 16))


def _draw_placeholder(screen, color, cx, cy, radius, selected):
    """Fallback circle when no portrait image is available."""
    if selected:
        pygame.draw.circle(screen, (255, 210, 40), (cx, cy), radius + 4)
    pygame.draw.circle(screen, color, (cx, cy), radius)
    pygame.draw.circle(screen, (200, 190, 160), (cx, cy), radius, 2)


def _draw_selected_ring(screen, x, y, w, h):
    """Golden glow rectangle around a portrait image when selected."""
    # Outer glow (soft, wider)
    glow_rect = pygame.Rect(x - 5, y - 5, w + 10, h + 10)
    pygame.draw.rect(screen, (255, 190, 20), glow_rect, 3, border_radius=6)
    # Inner tight ring
    inner_rect = pygame.Rect(x - 2, y - 2, w + 4, h + 4)
    pygame.draw.rect(screen, (255, 230, 80), inner_rect, 2, border_radius=4)


# ── Character ────────────────────────────────────────────────────────────────

class Character:
    """Represents a human character (detective or suspect)."""

    IMG_W = 55    # display width  for portrait
    IMG_H = 70    # display height for portrait

    def __init__(self, name, symbol, color, x=0, y=0):
        self.name        = name
        self.symbol      = symbol
        self.color       = color
        self.x           = x
        self.y           = y
        self.width       = self.IMG_W
        self.height      = self.IMG_H + 20   # extra room for name label
        self.side        = "left"
        self.selected    = False
        self.rect        = pygame.Rect(x, y, self.width, self.height)
        self.description = ""
        self.image       = None   # set externally: entity.image = pygame.Surface(...)

    def set_description(self, text):
        self.description = text

    def update_rect(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, font_label, font_sym=None):
        """
        Draw the character.
        font_sym is accepted but ignored (kept for API compatibility).
        """
        self.update_rect()
        cx = self.x + self.IMG_W // 2

        if self.image:
            # ── Portrait image ────────────────────────────────────────
            if self.selected:
                _draw_selected_ring(screen, self.x, self.y, self.IMG_W, self.IMG_H)
            screen.blit(self.image, (self.x, self.y))
        else:
            # ── Placeholder circle ────────────────────────────────────
            cy = self.y + self.IMG_H // 2
            _draw_placeholder(screen, self.color, cx, cy, 24, self.selected)

        # Name label below the portrait
        _draw_name(screen, font_label, self.name,
                   cx, self.y + self.IMG_H + 3, self.selected)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Evidence ─────────────────────────────────────────────────────────────────

class Evidence:
    """Represents a piece of evidence (item, not a human)."""

    IMG_W = 55
    IMG_H = 70

    def __init__(self, name, symbol, color, x=0, y=0):
        self.name        = name
        self.symbol      = symbol
        self.color       = color
        self.x           = x
        self.y           = y
        self.width       = self.IMG_W
        self.height      = self.IMG_H + 20
        self.side        = "left"
        self.selected    = False
        self.rect        = pygame.Rect(x, y, self.width, self.height)
        self.description = ""
        self.image       = None   # set externally

    def set_description(self, text):
        self.description = text

    def update_rect(self):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, font_label, font_sym=None):
        self.update_rect()
        cx = self.x + self.IMG_W // 2

        if self.image:
            # ── Evidence image ────────────────────────────────────────
            if self.selected:
                _draw_selected_ring(screen, self.x, self.y, self.IMG_W, self.IMG_H)
            screen.blit(self.image, (self.x, self.y))
        else:
            # ── Placeholder: diamond shape ────────────────────────────
            cy     = self.y + self.IMG_H // 2
            r      = 20
            points = [
                (cx,     cy - r),
                (cx + r, cy),
                (cx,     cy + r),
                (cx - r, cy),
            ]
            if self.selected:
                outer = [(cx, cy - r - 4), (cx + r + 4, cy),
                         (cx, cy + r + 4), (cx - r - 4, cy)]
                pygame.draw.polygon(screen, (255, 210, 40), outer)
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (200, 190, 160), points, 2)

        # Name label below
        _draw_name(screen, font_label, self.name,
                   cx, self.y + self.IMG_H + 3, self.selected)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)