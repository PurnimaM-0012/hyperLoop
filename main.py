# main.py
# Step 1: open a window and run the game loop.
# Step 2: a player that walks around the town and stops at walls.
# Step 3: an 80-second time loop that resets the player when it runs out.
# Step 4: machine parts to collect and install; install all three to clear the level.
# Step 5: progress that survives loop resets, saved to save.json.
# Run it with:  python main.py
#
# Keys:  WASD / arrows  move          F5  save progress
#        Esc            quit          R   DEBUG: reset the loop now
#        T              DEBUG: pretend you won a race (+20 s on future loops)

import os

import pygame

import settings
from machine import Machine, Part
from player import Player
from progress import Progress
from time_loop import TimeLoop, format_time
from town import Town

# The game as a whole is in one of these states. Later steps add RACING.
PLAYING = "playing"
LEVEL_CLEARED = "level_cleared"

# The save file sits next to this file, wherever you run the game from.
# __file__ is the path of main.py itself.
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.SAVE_FILE)


def solid_rects(town, parts):
    """Everything the player can't walk through this frame.

    Parts lying on the ground are solid, just like walls. Once picked up or
    installed they are no longer on the ground, so they stop blocking.
    """
    return town.walls + [part.rect for part in parts if part.state == Part.ON_GROUND]


def update_parts(player, parts, machine):
    """Pick up a part you're touching, install it on reaching the machine.

    Parts on the ground are solid, so the player stops exactly at their edge
    and never overlaps them. To detect "touching", we check a copy of the
    player's box grown by 2 pixels on every side (inflate(4, 4)).
    The machine is still a TRIGGER: you walk into it, it doesn't block you.
    """
    if player.carrying is None:
        # Hands free: pick up the first part on the ground we're touching.
        reach = player.rect.inflate(4, 4)
        for part in parts:
            if part.state == Part.ON_GROUND and reach.colliderect(part.rect):
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
    font = pygame.font.Font(None, 24)        # small text (FPS, HUD)
    timer_font = pygame.font.Font(None, 56)  # the big countdown
    message_font = pygame.font.Font(None, 40)
    win_font = pygame.font.Font(None, 80)

    # PERSISTENT state: load the save file if there is one.
    progress, loaded = Progress.load(SAVE_PATH)

    # LOOP state: everything below is wiped by reset_loop().
    town = Town()
    player = Player(settings.PLAYER_START)
    time_loop = TimeLoop(progress.loop_duration)
    parts = [Part(name, position, colour) for name, position, colour in settings.PARTS]
    machine = Machine(settings.MACHINE_RECT, len(parts))

    game_state = PLAYING
    level_id = progress.current_level  # the level being played right now

    # A short message in the middle of the screen ("Game saved", ...).
    message_text = ""
    message_colour = settings.TEXT
    message_time_left = 0  # seconds left to show it (0 = hidden)

    def show_message(text, colour=settings.TEXT):
        nonlocal message_text, message_colour, message_time_left
        message_text, message_colour = text, colour
        message_time_left = settings.RESET_MESSAGE_TIME

    if loaded:
        show_message("Save loaded")

    # ---------------- RESETTING THE LOOP ----------------
    # EVERYTHING that belongs to "this loop only" is reset here, in one place.
    # Note what is NOT here: 'progress'. That is the whole point of Step 5.
    def reset_loop(announce=True):
        player.reset()  # also drops any carried part
        # Each new loop lasts as long as Progress says, so race wins
        # (and the debug key T) make the NEXT loop longer.
        time_loop.duration = progress.loop_duration
        time_loop.reset()
        machine.reset()
        for part in parts:
            part.reset()
        if announce:
            show_message("The loop resets...", settings.TIMER_WARNING)

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
                elif event.key == pygame.K_F5:     # save progress
                    progress.save(SAVE_PATH)
                    show_message("Game saved")
                elif game_state == PLAYING and event.key == pygame.K_r:
                    reset_loop()                   # DEBUG: reset right away
                elif game_state == PLAYING and event.key == pygame.K_t:
                    # DEBUG: pretend you won a race. Only FUTURE loops get
                    # longer; the countdown running now doesn't change.
                    progress.add_loop_time(settings.DEBUG_RACE_BONUS)
                    show_message(f"+{settings.DEBUG_RACE_BONUS} s on future loops")
                elif game_state == LEVEL_CLEARED and event.key == pygame.K_RETURN:
                    # Replay the level just cleared; progress is kept.
                    reset_loop(announce=False)
                    game_state = PLAYING
                elif game_state == LEVEL_CLEARED and event.key == pygame.K_n:
                    # New game: wipe progress (and the save file) completely.
                    progress.new_game()
                    progress.save(SAVE_PATH)
                    level_id = progress.current_level
                    reset_loop(announce=False)
                    game_state = PLAYING
                    show_message("New game")

        # 2. UPDATE ---------------------------------------------------
        # Once the level is cleared, nothing moves and the timer stops.
        if game_state == PLAYING:
            player.update(dt, solid_rects(town, parts))
            update_parts(player, parts, machine)

            if machine.is_complete():
                # The level's sub-part is built: record it and save at once,
                # so a cleared level can never be lost.
                progress.clear_level(level_id)
                progress.save(SAVE_PATH)
                game_state = LEVEL_CLEARED
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
        timer_rect = timer_text.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 24))
        screen.blit(timer_text, timer_rect)

        # Under the countdown: how long a full loop lasts (persistent).
        loop_text = font.render(f"Loop: {format_time(progress.loop_duration)}", True, settings.TEXT)
        screen.blit(loop_text, loop_text.get_rect(midtop=(timer_rect.centerx, timer_rect.bottom + 2)))

        # Part counter and what you're carrying, in the top-right corner.
        top_right = settings.SCREEN_WIDTH - 24
        counter = font.render(f"Parts installed: {len(machine.installed)}/{machine.total_parts}",
                              True, settings.TEXT)
        screen.blit(counter, counter.get_rect(topright=(top_right, 24)))
        if player.carrying is not None:
            carrying = font.render(f"Carrying: {player.carrying.name}", True, player.carrying.colour)
            screen.blit(carrying, carrying.get_rect(topright=(top_right, 46)))

        # The level-cleared screen: darken everything, then show the text.
        if game_state == LEVEL_CLEARED:
            # SRCALPHA gives the surface see-through pixels; the 4th number
            # in the colour is opacity (0 = invisible, 255 = solid).
            shade = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 170))
            screen.blit(shade, (0, 0))
            centre_x, centre_y = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
            title = win_font.render(f"{settings.LEVEL_NAMES[level_id]} cleared!", True, settings.WIN)
            screen.blit(title, title.get_rect(center=(centre_x, centre_y - 30)))
            saved = font.render("Sub-part built. Progress saved.", True, settings.TEXT)
            screen.blit(saved, saved.get_rect(center=(centre_x, centre_y + 22)))
            hint = font.render("Enter: replay level     N: new game     Esc: quit", True, settings.TEXT)
            screen.blit(hint, hint.get_rect(center=(centre_x, centre_y + 50)))

        # The short message, in the middle of the screen (drawn last, on top).
        if message_time_left > 0:
            message = message_font.render(message_text, True, message_colour)
            centre = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 100)
            screen.blit(message, message.get_rect(center=centre))

        # Top-left: frames per second and the current level.
        fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, settings.TEXT)
        screen.blit(fps_text, (24, 24))
        level_text = font.render(f"Level: {settings.LEVEL_NAMES[level_id]}", True, settings.TEXT)
        screen.blit(level_text, (24, 46))

        # We drew on a hidden copy of the screen; flip() shows it all at once.
        pygame.display.flip()

    # The loop has ended: shut Pygame down cleanly.
    pygame.quit()


# Only run main() when this file is started directly (python main.py).
if __name__ == "__main__":
    main()
