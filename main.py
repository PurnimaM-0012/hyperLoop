# main.py
# Step 1: open a window and run the game loop.
# Step 2: a player that walks around the town and stops at walls.
# Step 3: an 80-second time loop that resets the player when it runs out.
# Run it with:  python main.py

import pygame

import settings
from player import Player
from time_loop import TimeLoop
from town import Town


def main():
    # Start up Pygame's modules (graphics, keyboard, fonts, sound...).
    pygame.init()

    # Create the window. 'screen' is the surface we draw on every frame.
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption(settings.TITLE)

    # The clock controls the frame rate and tells us how much time passed.
    clock = pygame.time.Clock()

    # Fonts: None = Pygame's built-in font; the number is the size.
    font = pygame.font.Font(None, 24)        # small debug text (FPS)
    timer_font = pygame.font.Font(None, 56)  # the big countdown
    message_font = pygame.font.Font(None, 40)

    # Create the game objects once, before the loop starts.
    town = Town()
    player = Player(settings.PLAYER_START)
    time_loop = TimeLoop(settings.LOOP_DURATION)

    # Seconds left to show the "loop resets" message (0 = hidden).
    message_time_left = 0

    # ---------------- RESETTING THE LOOP ----------------
    # EVERYTHING that belongs to "this loop only" is reset here, in one place.
    # The timer running out calls it now; death will call it in Step 10.
    def reset_loop():
        # 'nonlocal' lets this inner function change the variable defined
        # in main() above, instead of creating a new local one.
        nonlocal message_time_left
        player.reset()
        time_loop.reset()
        message_time_left = settings.RESET_MESSAGE_TIME

    running = True

    # ---------------- THE GAME LOOP ----------------
    while running:
        # clock.tick() waits so we never run faster than FPS, and returns how
        # many milliseconds passed since the last frame. We convert to seconds.
        # 'dt' (delta time) keeps movement and the timer in REAL seconds on
        # fast and slow computers alike.
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:      # DEBUG: reset right away
                    reset_loop()

        # 2. UPDATE ---------------------------------------------------
        player.update(dt, town.walls)

        # Count down; update() returns True on the frame time runs out.
        if time_loop.update(dt):
            reset_loop()

        # Count the message down until it disappears.
        message_time_left = max(0, message_time_left - dt)

        # 3. DRAW -----------------------------------------------------
        # Clear the whole screen first, or the last frame would smear.
        screen.fill(settings.BACKGROUND)

        # Draw back-to-front: the town first, then the player on top of it.
        town.draw(screen)
        player.draw(screen)

        # The countdown, centred at the top. Red in the last few seconds.
        if time_loop.time_left <= settings.WARNING_TIME:
            timer_colour = settings.TIMER_WARNING
        else:
            timer_colour = settings.TEXT
        timer_text = timer_font.render(time_loop.display_text(), True, timer_colour)
        # get_rect(midtop=...) positions the text by its top-centre point,
        # which makes centring easy.
        screen.blit(timer_text, timer_text.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 24)))

        # The "loop resets" message, in the middle of the screen.
        if message_time_left > 0:
            message = message_font.render("The loop resets...", True, settings.TIMER_WARNING)
            centre = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 60)
            screen.blit(message, message.get_rect(center=centre))

        # Draw the current frames per second in the top-left corner.
        fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, settings.TEXT)
        screen.blit(fps_text, (24, 24))

        # We drew on a hidden copy of the screen; flip() shows it all at once.
        pygame.display.flip()

    # The loop has ended: shut Pygame down cleanly.
    pygame.quit()


# Only run main() when this file is started directly (python main.py).
if __name__ == "__main__":
    main()
