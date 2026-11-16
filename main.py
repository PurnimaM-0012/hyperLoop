# main.py
# Step 1: open a window and run the game loop.
# Step 2: a player that walks around the town and stops at walls.
# Run it with:  python main.py

import pygame

import settings
from player import Player
from town import Town


def main():
    # Start up Pygame's modules (graphics, keyboard, fonts, sound...).
    pygame.init()

    # Create the window. 'screen' is the surface we draw on every frame.
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption(settings.TITLE)

    # The clock controls the frame rate and tells us how much time passed.
    clock = pygame.time.Clock()

    # A small font for debug text such as the frames-per-second counter.
    font = pygame.font.Font(None, 24)  # None = Pygame's built-in font

    # Create the game objects once, before the loop starts.
    town = Town()
    player = Player(settings.PLAYER_START)

    running = True

    # ---------------- THE GAME LOOP ----------------
    while running:
        # clock.tick() waits so we never run faster than FPS, and returns how
        # many milliseconds passed since the last frame. We convert to seconds.
        # 'dt' (delta time) lets later steps move things at the same speed on
        # fast and slow computers, and will drive the 80-second loop timer.
        dt = clock.tick(settings.FPS) / 1000

        # Safety cap: if the game freezes for a moment (e.g. while you drag
        # the window), dt could be a whole second. Moving 200 px in one jump
        # could skip straight through a wall, so we never allow a huge step.
        dt = min(dt, settings.MAX_DT)

        # 1. HANDLE INPUT ---------------------------------------------
        # Pygame collects everything that happened (key presses, mouse,
        # the window's close button) into a queue of "events".
        for event in pygame.event.get():
            if event.type == pygame.QUIT:          # the window's X button
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 2. UPDATE ---------------------------------------------------
        player.update(dt, town.walls)

        # 3. DRAW -----------------------------------------------------
        # Clear the whole screen first, or the last frame would smear.
        screen.fill(settings.BACKGROUND)

        # Draw back-to-front: the town first, then the player on top of it.
        town.draw(screen)
        player.draw(screen)

        # Draw the current frames per second in the top-left corner.
        fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, settings.TEXT)
        screen.blit(fps_text, (10, 10))

        # We drew on a hidden copy of the screen; flip() shows it all at once.
        pygame.display.flip()

    # The loop has ended: shut Pygame down cleanly.
    pygame.quit()


# Only run main() when this file is started directly (python main.py).
if __name__ == "__main__":
    main()
