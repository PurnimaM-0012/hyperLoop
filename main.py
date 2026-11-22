# main.py
# Starts the game and runs the game loop. Everything you SEE is a scene
# (scenes.py): the menu, a level, and later a race. This file just runs
# whichever scene is current.
#
# Run it with:  python main.py
#
# Keys in a level:  WASD / arrows  move          F5   save progress
#                   Q              drop the last item picked up
#                   Esc            menu          R    DEBUG: reset the loop now
#                   B              DEBUG: one more bag slot
#                   C              DEBUG: drive the car on the test track (C or Esc to come back)
#
# Keys on the track: W/S throttle and brake, A/D steer, Space handbrake (drift)
#                    Tab live tuning panel ([ ] choose, - = change, Backspace reset, F6 save)
#                   T              DEBUG: pretend you won a race (+20 s now and on future loops)

import os

import pygame

import settings
from progress import Progress
from scenes import MenuScene
from tuning import TuningPanel


class Game:
    """Things every scene needs: fonts, progress, and which scene is current."""

    def __init__(self):
        # Fonts: None = Pygame's built-in font; the number is the size.
        self.fonts = {
            "small": pygame.font.Font(None, 24),
            "medium": pygame.font.Font(None, 40),
            "timer": pygame.font.Font(None, 48),
            "big": pygame.font.Font(None, 80),
        }
        # PERSISTENT state, loaded from the save file if there is one.
        self.progress, _ = Progress.load(settings.SAVE_PATH)
        self.running = True
        # One live tuning panel for the whole session (Tab on the race track),
        # so it remembers the starting values from settings.py.
        self.tuning = TuningPanel()
        self.scene = MenuScene(self)

    def save_exists(self):
        return os.path.exists(settings.SAVE_PATH)


def main():
    # Start up Pygame's modules (graphics, keyboard, fonts, sound...).
    pygame.init()

    # Create the window. 'screen' is the surface we draw on every frame.
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption(settings.TITLE)

    # The clock controls the frame rate and tells us how much time passed.
    clock = pygame.time.Clock()
    game = Game()

    # ---------------- THE GAME LOOP ----------------
    while game.running:
        # 'dt' (delta time): seconds since the last frame, so movement and
        # timers run in REAL seconds on fast and slow computers alike.
        dt = clock.tick(settings.FPS) / 1000
        # Safety cap: a long freeze (e.g. dragging the window) must not
        # produce one giant step that skips through a wall.
        dt = min(dt, settings.MAX_DT)

        # 1. HANDLE INPUT: the window's X quits; everything else goes to the scene.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            else:
                game.scene.handle_event(event)

        # 2. UPDATE and 3. DRAW whichever scene is current.
        game.scene.update(dt)
        game.scene.draw(screen)

        # Frames per second, top-left, on top of every scene.
        fps_text = game.fonts["small"].render(f"FPS: {clock.get_fps():.0f}", True, settings.DIM_TEXT)
        screen.blit(fps_text, (16, 12))

        # We drew on a hidden copy of the screen; flip() shows it all at once.
        pygame.display.flip()

    # The loop has ended: shut Pygame down cleanly.
    pygame.quit()


# Only run main() when this file is started directly (python main.py).
if __name__ == "__main__":
    main()
