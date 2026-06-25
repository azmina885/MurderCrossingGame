import pygame
import sys
from game_manager import GameManager

# ── Window settings ────────────────────────────────────────────────────────
TITLE  = "Murder Across the River: The Blackwood Case"
WIDTH  = 960
HEIGHT = 680
FPS    = 60


def load_fonts():
    """Load system fonts. Falls back gracefully if a specific font is missing."""
    def F(size, bold=False):
        try:
            return pygame.font.SysFont("arial", size, bold=bold)
        except Exception:
            return pygame.font.Font(None, size)

    return {
        "big":    F(52, bold=True),
        "medium": F(34, bold=True),
        "small":  F(24),
        "tiny":   F(18),
    }


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock  = pygame.time.Clock()
    fonts  = load_fonts()

    gm = GameManager(screen, fonts)

    while True:
        dt = clock.tick(FPS)   # ms elapsed since last frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            gm.handle_event(event)

        gm.update(dt)
        gm.draw()


if __name__ == "__main__":
    main()