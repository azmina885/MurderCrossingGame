import os
import pygame


def _load_boat_image(w, h):
    """Load boat.png from the images/ folder. Returns None if missing."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "images", "boat.png")
    if not os.path.isfile(path):
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(surf, (w, h))
    except Exception:
        return None


class Boat:
    """
    Handles the investigation boat.
    Capacity is set externally by game_manager:
      Level 1 → capacity 2  (Detective + 1)
      Level 2 → capacity 3  (Detective + 2)
      Level 3 → capacity 4  (Detective + 3)
    Detective MUST be on board to sail.
    """

    BOAT_H = 90

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h

        self.height   = self.BOAT_H
        self.capacity = 2          # default; overridden by game_manager after init

        self._base_w  = 170        # width for capacity-2
        self._wide_w  = 240        # width for capacity-3
        self._wider_w = 310        # width for capacity-4
        self.width    = self._base_w

        self.left_x   = 200
        self.right_x  = screen_w - 200 - self.width
        self.x        = self.left_x
        self.y        = screen_h // 2 + 10

        self.side     = "left"
        self.moving   = False
        self.speed    = 5
        self.target_x = self.left_x

        self.passengers = []

        self.rect  = pygame.Rect(self.x, self.y, self.width, self.height)
        self.image = None

    def _update_size(self):
        """Resize boat and reload image based on current capacity."""
        if self.capacity >= 4:
            self.width = self._wider_w
        elif self.capacity >= 3:
            self.width = self._wide_w
        else:
            self.width = self._base_w
        self.right_x = self.screen_w - 200 - self.width
        self.image   = _load_boat_image(self.width, self.height)
        self.rect    = pygame.Rect(self.x, self.y, self.width, self.height)

    # ── Boarding / Disembarking ──────────────────────────────────────────

    def load(self, entity):
        if entity in self.passengers:
            return False
        if len(self.passengers) >= self.capacity:
            return False
        self.passengers.append(entity)
        entity.side = "boat"
        self._arrange()
        return True

    def unload(self, entity):
        if entity in self.passengers:
            self.passengers.remove(entity)
            self._arrange()

    def unload_all(self):
        for e in self.passengers:
            e.side = self.side
        self.passengers.clear()

    def _arrange(self):
        """Position passengers sitting on top of the boat — supports up to 4."""
        slot_w = 55
        gap    = 8
        n      = len(self.passengers)
        if n == 0:
            return
        total_w = n * slot_w + (n - 1) * gap
        start_x = self.x + (self.width - total_w) // 2
        for i, e in enumerate(self.passengers):
            e.x = start_x + i * (slot_w + gap)
            e.y = self.y - 70
            e.update_rect()

    # ── Movement ─────────────────────────────────────────────────────────

    def move(self):
        detective_aboard = any(p.name == "Detective James" for p in self.passengers)
        if not detective_aboard:
            return False
        self.target_x = self.right_x if self.side == "left" else self.left_x
        self.moving   = True
        return True

    def update(self):
        if not self.moving:
            return False

        if self.x < self.target_x:
            self.x = min(self.x + self.speed, self.target_x)
        else:
            self.x = max(self.x - self.speed, self.target_x)

        self._arrange()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.x == self.target_x:
            self.moving = False
            self.side   = "right" if self.target_x == self.right_x else "left"
            self.unload_all()
            return True

        return False

    # ── Draw ─────────────────────────────────────────────────────────────

    def draw(self, screen, font_tiny):
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            pygame.draw.ellipse(screen, (90, 55, 25), self.rect)
            pygame.draw.ellipse(screen, (50, 25,  5), self.rect, 3)
            lbl = font_tiny.render("BOAT", True, (255, 210, 80))
            screen.blit(lbl, (self.x + (self.width  - lbl.get_width())  // 2,
                               self.y + (self.height - lbl.get_height()) // 2))
        # NOTE: _arrange() intentionally NOT called here — draw() must not mutate state.