# main.py
# Step 1: open a window and run the game loop.
# Step 2: a player that walks around the town and stops at walls.
# Step 3: an 80-second time loop that resets the player when it runs out.
# Step 4: machine parts to collect and install; install all three to win.
# Run it with:  python main.py

import pygame

import settings
from machine import Machine, Part
from player import Player
from time_loop import TimeLoop
from town import Town

# The game as a whole is in one of these states. Step 6 will add RACING.
PLAYING = "playing"
WON = "won"


def update_parts(player, parts, machine):
    """Pick up a part on contact, install it on reaching the machine.

    Parts and the machine are TRIGGERS: overlapping them makes something
    happen, but they never block movement the way walls do.
    """
    if player.carrying is None:
        # Hands free: pick up the first part on the ground we're touching.
        for part in parts:
            if part.state == Part.ON_GROUND and player.rect.colliderect(part.rect):
                part.state = Part.CARRIED
                player.carrying = part
                break  # only one part at a time
    elif player.rect.colliderect(machine.rect):
        # Carrying a part and touching the machine: install it.
        machine.install(player.carrying)
        player.carrying = None


def main():
    # Start up Pygame's modules (graphics, keyboard, fonts, sound...).
    pygame.init()

    # Create the window. 'screen' is the surface we draw on every frame.
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption(settings.TITLE)

    # The clock controls the frame rate and tells us how much time passed.
    clock = pygame.time.Clock()

    # Fonts: None = Pygame's built-in font; the number is the size.
    font = pygame.font.Font(None, 24)        # small text (FPS, part counter)
    timer_font = pygame.font.Font(None, 56)  # the big countdown
    message_font = pygame.font.Font(None, 40)
    win_font = pygame.font.Font(None, 80)

    # Create the game objects once, before the loop starts.
    town = Town()
    player = Player(settings.PLAYER_START)
    time_loop = TimeLoop(settings.LOOP_DURATION)
    parts = [Part(name, position, colour) for name, position, colour in settings.PARTS]
    machine = Machine(settings.MACHINE_RECT, len(parts))

    game_state = PLAYING
    # Seconds left to show the "loop resets" message (0 = hidden).
    message_time_left = 0

    # ---------------- RESETTING THE LOOP ----------------
    # EVERYTHING that belongs to "this loop only" is reset here, in one place.
    # The timer running out calls it now; death will call it in Step 10.
    def reset_loop(show_message=True):
        # 'nonlocal' lets this inner function change the variable defined
        # in main() above, instead of creating a new local one.
        nonlocal message_time_left
        player.reset()  # also drops any carried part
        time_loop.reset()
        machine.reset()
        for part in parts:
            part.reset()
        message_time_left = settings.RESET_MESSAGE_TIME if show_message else 0

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
                elif event.key == pygame.K_r and game_state == PLAYING:
                    reset_loop()                   # DEBUG: reset right away
                elif event.key == pygame.K_RETURN and game_state == WON:
                    reset_loop(show_message=False)  # play again
                    game_state = PLAYING

        # 2. UPDATE ---------------------------------------------------
        # Once you've won, nothing moves and the timer stops.
        if game_state == PLAYING:
            player.update(dt, town.walls)
            update_parts(player, parts, machine)

            if machine.is_complete():
                game_state = WON
            # Count down; update() returns True on the frame time runs out.
            elif time_loop.update(dt):
                reset_loop()

        # Count the message down until it disappears.
        message_time_left = max(0, message_time_left - dt)

        # 3. DRAW -----------------------------------------------------
        # Clear the whole screen first, or the last frame would smear.
        screen.fill(settings.BACKGROUND)

        # Draw back-to-front: town, machine and parts, then the player on top.
        town.draw(screen)
        machine.draw(screen)
        for part in parts:
            part.draw(screen)
        player.draw(screen)
        if player.carrying is not None:
            # Show the carried part just above the player's head.
            above_head = (player.rect.centerx, player.rect.top - 12)
            player.carrying.draw_at(screen, above_head)

        # The countdown, centred at the top. Red in the last few seconds.
        if time_loop.time_left <= settings.WARNING_TIME:
            timer_colour = settings.TIMER_WARNING
        else:
            timer_colour = settings.TEXT
        timer_text = timer_font.render(time_loop.display_text(), True, timer_colour)
        # get_rect(midtop=...) positions the text by its top-centre point,
        # which makes centring easy.
        screen.blit(timer_text, timer_text.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 24)))

        # Part counter and what you're carrying, in the top-right corner.
        top_right = settings.SCREEN_WIDTH - 24
        counter = font.render(f"Parts installed: {len(machine.installed)}/{machine.total_parts}",
                              True, settings.TEXT)
        screen.blit(counter, counter.get_rect(topright=(top_right, 24)))
        if player.carrying is not None:
            carrying = font.render(f"Carrying: {player.carrying.name}", True, player.carrying.colour)
            screen.blit(carrying, carrying.get_rect(topright=(top_right, 46)))

        # The "loop resets" message, in the middle of the screen.
        if message_time_left > 0:
            message = message_font.render("The loop resets...", True, settings.TIMER_WARNING)
            centre = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 60)
            screen.blit(message, message.get_rect(center=centre))

        # The win screen: darken everything, then show the message on top.
        if game_state == WON:
            # SRCALPHA gives the surface see-through pixels; the 4th number
            # in the colour is opacity (0 = invisible, 255 = solid).
            shade = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            centre_x, centre_y = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
            title = win_font.render("You escaped!", True, settings.WIN)
            screen.blit(title, title.get_rect(center=(centre_x, centre_y - 20)))
            hint = font.render("Enter: play again     Esc: quit", True, settings.TEXT)
            screen.blit(hint, hint.get_rect(center=(centre_x, centre_y + 36)))

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
