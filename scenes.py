# scenes.py
# The game's screens. Each SCENE has the same three methods:
#   handle_event(event)  - respond to a key press
#   update(dt)           - move things forward by dt seconds
#   draw(screen)         - draw itself
# main.py just runs whichever scene is current. To change screens, a scene
# sets game.scene to a new scene. A race works the same way: the level
# hands itself to the RaceScene, which hands control back when it's over.

import math
import random

import pygame

import settings
from bag import Bag
from camera import Camera
from car import Car
from level import Level, load_track, read_level_name
from machine import Part
from player import Player
from time_loop import TimeLoop, format_time


# =====================================================================
#  MENU
# =====================================================================

class MenuScene:
    # The menu has three pages ("modes").
    MAIN = "main"        # Continue / New game / Replay a level / Quit
    REPLAY = "replay"    # the list of cleared levels
    CONFIRM = "confirm"  # "This erases your progress. Are you sure?"

    def __init__(self, game):
        self.game = game
        self.mode = MenuScene.MAIN
        self.selected = 0  # index of the highlighted item
        self.items = self.main_items()

    def main_items(self):
        items = []
        if self.game.save_exists():
            items.append("Continue")
        items.append("New game")
        if self.game.progress.cleared_levels:
            items.append("Replay a level")
        items.append("Quit")
        return items

    def open_page(self, mode, items):
        self.mode = mode
        self.items = items
        self.selected = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.mode == MenuScene.CONFIRM:
            if event.key == pygame.K_y:
                self.start_new_game()
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self.open_page(MenuScene.MAIN, self.main_items())
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            # % (remainder) wraps around: going up from the top lands on the bottom.
            self.selected = (self.selected - 1) % len(self.items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.items)
        elif event.key == pygame.K_RETURN:
            self.choose(self.items[self.selected])
        elif event.key == pygame.K_ESCAPE:
            if self.mode == MenuScene.MAIN:
                self.game.running = False   # Esc on the main page quits
            else:
                self.open_page(MenuScene.MAIN, self.main_items())

    def choose(self, item):
        progress = self.game.progress
        if self.mode == MenuScene.MAIN:
            if item == "Continue":
                self.game.scene = LevelScene(self.game, progress.current_level)
            elif item == "New game":
                if self.game.save_exists():
                    self.open_page(MenuScene.CONFIRM, [])  # ask first
                else:
                    self.start_new_game()
            elif item == "Replay a level":
                names = [read_level_name(level_id) for level_id in progress.cleared_levels]
                self.open_page(MenuScene.REPLAY, names + ["Back"])
            elif item == "Quit":
                self.game.running = False
        elif self.mode == MenuScene.REPLAY:
            if item == "Back":
                self.open_page(MenuScene.MAIN, self.main_items())
            else:
                level_id = progress.cleared_levels[self.selected]
                self.game.scene = LevelScene(self.game, level_id)

    def start_new_game(self):
        progress = self.game.progress
        progress.new_game()
        progress.save(settings.SAVE_PATH)  # overwrite the old save
        self.game.scene = LevelScene(self.game, progress.current_level)

    def update(self, dt):
        pass  # nothing moves on the menu

    def draw(self, screen):
        fonts = self.game.fonts
        screen.fill(settings.BACKGROUND)
        centre_x = settings.SCREEN_WIDTH // 2

        title = fonts["big"].render("TIME LOOP", True, settings.TEXT)
        screen.blit(title, title.get_rect(center=(centre_x, 150)))

        if self.mode == MenuScene.CONFIRM:
            lines = [("This erases your progress.", settings.TEXT),
                     ("Start a new game?  Y / N", settings.HIGHLIGHT)]
            for i, (text, colour) in enumerate(lines):
                surface = fonts["medium"].render(text, True, colour)
                screen.blit(surface, surface.get_rect(center=(centre_x, 280 + i * 44)))
            return

        if self.mode == MenuScene.REPLAY:
            heading = fonts["small"].render("Replay a cleared level", True, settings.DIM_TEXT)
            screen.blit(heading, heading.get_rect(center=(centre_x, 230)))

        for i, item in enumerate(self.items):
            selected = (i == self.selected)
            text = f"> {item} <" if selected else item
            colour = settings.HIGHLIGHT if selected else settings.DIM_TEXT
            surface = fonts["medium"].render(text, True, colour)
            screen.blit(surface, surface.get_rect(center=(centre_x, 280 + i * 48)))

        hint = fonts["small"].render("Up / Down: choose     Enter: select     Esc: back",
                                     True, settings.DIM_TEXT)
        screen.blit(hint, hint.get_rect(center=(centre_x, settings.SCREEN_HEIGHT - 40)))


# =====================================================================
#  PLAYING A LEVEL
# =====================================================================

def solid_rects(level, area_name):
    """Everything the player can't walk through in this area right now.

    Parts lying on the ground are solid, just like walls. Once picked up or
    installed they are no longer on the ground, so they stop blocking.
    A part you've just dropped doesn't block you until you step away from it
    (otherwise it would appear inside you and you'd be stuck).
    """
    area = level.areas[area_name]
    ground_parts = [part.rect for part in level.parts
                    if part.area == area_name and part.state == Part.ON_GROUND
                    and not part.just_dropped]
    return area.walls + ground_parts


def update_parts(player, parts, machine):
    """Pick up parts you're touching, install them on reaching the machine.

    'parts' are the parts in the player's current area, and 'machine' is
    None when the machine is in a different area.
    Parts on the ground are solid, so the player stops exactly at their edge
    and never overlaps them. To detect "touching", we check a copy of the
    player's box grown by 2 pixels on every side (inflate(4, 4)).
    The machine is still a TRIGGER: you walk into it, it doesn't block you.
    """
    reach = player.rect.inflate(4, 4)
    bag = player.bag

    for part in parts:
        if part.state != Part.ON_GROUND:
            continue
        if part.just_dropped:
            # Stepped away from a part you dropped: it's a normal part again.
            if not reach.colliderect(part.rect):
                part.just_dropped = False
        elif bag.has_room() and reach.colliderect(part.rect):
            # Touching a part and the bag has a free slot: pick it up.
            part.state = Part.CARRIED
            bag.add(part)

    if machine is not None and player.rect.colliderect(machine.rect):
        # Touching the machine: install EVERY part in the bag.
        for part in bag.parts():
            bag.remove(part)
            machine.install(part)


def darken(screen):
    """Dim everything already drawn, so an overlay's text stands out."""
    # SRCALPHA gives the surface see-through pixels; the 4th number
    # in the colour is opacity (0 = invisible, 255 = solid).
    shade = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 170))
    screen.blit(shade, (0, 0))


class LevelScene:
    PLAYING = "playing"
    RACE_PROMPT = "race_prompt"  # "Race? Y / N" is on screen; the timer is paused
    CLEARED = "cleared"

    def __init__(self, game, level_id):
        self.game = game
        self.progress = game.progress  # PERSISTENT: never reset below

        # LOOP state: everything reset_loop() puts back.
        self.level = Level(level_id)
        # The bag's SIZE is persistent (it grows as you clear levels); its
        # loop items (parts) are emptied by every loop reset.
        self.player = Player(self.level.start, Bag(self.progress.bag_capacity))
        self.time_loop = TimeLoop(self.loop_length())
        # One race per loop: set once you race (or say no), cleared by reset_loop().
        self.race_done = False
        self.area_name = self.level.start_area  # the area (map) the player is in
        # A portal only works once you've stepped OFF a portal. Without this,
        # you'd arrive standing on the other portal and bounce straight back.
        self.portal_ready = True

        # A replay is playing any level other than the one you're up to.
        # Replays don't show sub-parts built in other levels on the machine.
        self.is_replay = (level_id != self.progress.current_level)
        # Race bonuses only count on your FIRST visit to a level, before you
        # leave it cleared (design doc). Checked once, when the visit starts,
        # so racing from the "cleared" screen of that same visit still counts,
        # but a replay of a cleared level is only practice.
        self.bonus_counts = level_id not in self.progress.cleared_levels

        self.camera = Camera()
        self.state = LevelScene.PLAYING
        self.next_level = None  # set when a level is cleared and another follows
        self.elapsed = 0        # seconds since the scene began (for the portal glow)
        self.message_text = ""
        self.message_colour = settings.TEXT
        self.message_time_left = 0

    # ---------------- helpers ----------------

    @property
    def area(self):
        """The Area object the player is in. A @property is read like a
        variable (self.area) but works it out each time it's used."""
        return self.level.areas[self.area_name]

    def loop_length(self):
        """This level's loop length, worked out from Progress (see progress.py)."""
        return self.progress.loop_length(self.level.id, self.level.loop_cap)

    def can_race(self):
        """True if this level has a race and you haven't had this loop's yet.
        (The Prison has no race: its level file has "track": null.)"""
        return self.level.track is not None and not self.race_done

    def race_slot(self):
        """The race gets the last 40% of the loop: 32 s of an 80 s loop."""
        return settings.RACE_SHARE * self.time_loop.duration

    def show_message(self, text, colour=settings.TEXT):
        self.message_text, self.message_colour = text, colour
        self.message_time_left = settings.MESSAGE_TIME

    def reset_loop(self, announce=True):
        """Reset EVERYTHING that belongs to this loop only. Never 'progress'."""
        self.area_name = self.level.start_area  # every loop starts at the machine
        self.player.reset()  # back to S; parts leave the bag (they go home below)
        self.portal_ready = True
        self.race_done = False  # a new loop brings a new race
        # Each new loop lasts as long as Progress says, so race wins make
        # the NEXT loop longer.
        self.time_loop.duration = self.loop_length()
        self.time_loop.reset()
        self.level.machine.reset()
        for part in self.level.parts:
            part.reset()
        if announce:
            self.show_message("The loop resets...", settings.TIMER_WARNING)

    def use_portal(self):
        """Travel to the other area when the player stands on a portal."""
        portal = self.area.portal
        if portal is None or not self.level.portal_links:
            return
        standing_on_it = portal.collidepoint(self.player.rect.center)
        if not standing_on_it:
            self.portal_ready = True  # stepped off: portals work again
        elif self.portal_ready:
            destination = self.level.portal_links[self.area_name]
            self.area_name = destination
            # Arrive on the destination's portal, with everything in the bag.
            self.player.teleport(self.level.portal_arrival(destination))
            self.portal_ready = False  # must step off before it works again

    def drop_item(self):
        """Q: put the most recently picked-up item on the ground where you stand."""
        bag = self.player.bag
        if not bag.items:
            self.show_message("The bag is empty")
            return
        item = bag.take_last()
        item.drop_at(self.player.rect.center, self.area_name)
        self.show_message(f"Dropped {item.name}")

    def clear_level(self):
        """The level's sub-part is built: record it, save, and find what's next."""
        was_current = (self.level.id == self.progress.current_level)
        self.progress.clear_level(self.level.id)
        # Save at once, so a cleared level can never be lost.
        self.progress.save(settings.SAVE_PATH)
        # Clearing your current level unlocks the next one. A replay of an
        # earlier level doesn't, so it just goes back to the menu.
        if was_current and self.progress.current_level != self.level.id:
            self.next_level = self.progress.current_level
        self.state = LevelScene.CLEARED

    # ---------------- racing ----------------

    def start_race(self):
        """Hand over to the race track. This scene waits, paused, until
        the RaceScene calls race_over()."""
        self.race_done = True
        self.game.scene = RaceScene(self.game, self, self.level.track, self.race_slot())

    def record_race_win(self, bonus):
        """Called by the RaceScene on a win. Keeps the bonus if it's this
        level's best, and saves at once. Returns True for a new best.
        A practice race (a replay of a cleared level) changes nothing."""
        if not self.bonus_counts:
            return False
        new_best = self.progress.record_race_win(self.level.id, bonus)
        self.progress.save(settings.SAVE_PATH)
        return new_best

    def race_over(self, won, bonus):
        """Called by the RaceScene when the player leaves the result screen."""
        self.game.scene = self
        if self.state == LevelScene.CLEARED:
            return  # raced after clearing the level: back to the cleared screen
        self.state = LevelScene.PLAYING
        if won:
            # Future loops are longer (if this was a new best)...
            self.time_loop.duration = self.loop_length()
            # ...and THIS loop goes on, with the clock SET to the bonus
            # (not the time left + the bonus: the race used up that time).
            self.time_loop.time_left = bonus
            self.show_message(f"{format_time(bonus)} on the clock", settings.WIN)
        else:
            # The race was the end of the loop: no time is left.
            self.reset_loop()

    # ---------------- the three scene methods ----------------

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.scene = MenuScene(self.game)
        elif event.key == pygame.K_F5:             # save progress
            self.progress.save(settings.SAVE_PATH)
            self.show_message("Game saved")
        elif self.state == LevelScene.RACE_PROMPT:
            if event.key == pygame.K_y:
                self.start_race()
            elif event.key == pygame.K_n:
                # No race this loop: stay in town until the loop ends.
                self.race_done = True
                self.state = LevelScene.PLAYING
        elif self.state == LevelScene.PLAYING and event.key == pygame.K_q:
            self.drop_item()
        elif self.state == LevelScene.PLAYING and event.key == pygame.K_c:
            # Skip to the race: the time until the race slot is lost.
            if self.level.track is None:
                self.show_message("There's no race in this level")
            elif self.race_done:
                self.show_message("Only one race per loop")
            else:
                self.time_loop.time_left = self.race_slot()
                self.start_race()
        elif self.state == LevelScene.PLAYING and event.key == pygame.K_r:
            self.reset_loop()                      # DEBUG: reset right away
        elif self.state == LevelScene.PLAYING and event.key == pygame.K_b:
            # DEBUG: one more bag slot, saved like real progress.
            self.progress.bag_capacity += 1
            self.player.bag.capacity = self.progress.bag_capacity
            self.show_message(f"Bag: {self.player.bag.capacity} slots")
        elif self.state == LevelScene.CLEARED and event.key == pygame.K_r and self.can_race():
            # Sub-part built before the race: you may still race for the bonus.
            self.start_race()
        elif self.state == LevelScene.CLEARED and event.key == pygame.K_RETURN:
            if self.next_level is not None:
                self.game.scene = LevelScene(self.game, self.next_level)
            else:
                self.game.scene = MenuScene(self.game)
        elif self.state == LevelScene.CLEARED and event.key == pygame.K_m:
            self.game.scene = MenuScene(self.game)

    def update(self, dt):
        self.elapsed += dt
        if self.state == LevelScene.PLAYING:
            level = self.level
            self.player.update(dt, solid_rects(level, self.area_name))
            self.use_portal()

            # Only the parts in this area can be picked up, and the machine
            # only works if it's in this area too.
            parts_here = [part for part in level.parts if part.area == self.area_name]
            machine_here = level.machine if self.area_name == level.machine_area else None
            update_parts(self.player, parts_here, machine_here)

            if level.machine.is_complete():
                self.clear_level()
            # Count down; update() returns True on the frame time runs out.
            elif self.time_loop.update(dt):
                self.reset_loop()
            elif self.can_race() and self.time_loop.time_left <= self.race_slot():
                # The race slot has begun: ask. Snap the clock to exactly the
                # slot so the race gets its full time, whatever the frame timing.
                # In RACE_PROMPT this method stops counting down, so the timer
                # is paused while the question is on screen.
                self.time_loop.time_left = self.race_slot()
                self.state = LevelScene.RACE_PROMPT

        self.message_time_left = max(0, self.message_time_left - dt)

    def draw(self, screen):
        level, player, camera, area = self.level, self.player, self.camera, self.area

        # Point the camera at the player, then draw the WORLD through it.
        camera.follow(player.rect, area.width, area.height)
        screen.fill(settings.BACKGROUND)  # shows around maps smaller than the window
        screen.blit(area.background, camera.to_screen(area.background.get_rect()))

        if area.portal is not None and level.portal_links:
            self.draw_portal_glow(screen, camera.to_screen(area.portal))
        if self.area_name == level.machine_area:
            # Sub-parts from OTHER cleared levels (persistent) sit on the
            # machine, but only when playing your current level, not a replay.
            if self.is_replay:
                built = 0
            else:
                built = len([lid for lid in self.progress.cleared_levels if lid != level.id])
            level.machine.draw(screen, camera, built)
        for part in level.parts:
            if part.area == self.area_name:
                part.draw(screen, camera)
        player.draw(screen, camera)
        # Show what's in the bag as a row of small squares above the player.
        items = player.bag.items
        if items:
            on_screen = camera.to_screen(player.rect)
            spacing = settings.PART_SIZE + 2
            first_x = on_screen.centerx - (len(items) - 1) * spacing / 2
            for i, item in enumerate(items):
                item.draw_at(screen, (first_x + i * spacing, on_screen.top - 12))

        # SCREEN things (they don't scroll): the HUD and the overlays.
        self.draw_hud(screen)
        if self.state == LevelScene.RACE_PROMPT:
            self.draw_race_prompt(screen)
        elif self.state == LevelScene.CLEARED:
            self.draw_cleared(screen)
        if self.message_time_left > 0:
            message = self.game.fonts["medium"].render(self.message_text, True, self.message_colour)
            centre = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 100)
            screen.blit(message, message.get_rect(center=centre))

    def draw_portal_glow(self, screen, portal_rect):
        # math.sin swings smoothly between -1 and 1; turn that into 0..1
        # so the ring grows and shrinks about once a second.
        pulse = (math.sin(self.elapsed * 6) + 1) / 2
        ring = portal_rect.inflate(4 + pulse * 8, 4 + pulse * 8)
        pygame.draw.rect(screen, settings.PORTAL_GLOW, ring, width=2, border_radius=6)

    def draw_hud(self, screen):
        """The bar at the top: level, timer, loop length, parts."""
        fonts = self.game.fonts
        bar = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.HUD_HEIGHT)
        pygame.draw.rect(screen, settings.HUD_BAR, bar)

        # Centre: the countdown, red in the last few seconds.
        if self.time_loop.time_left <= settings.WARNING_TIME:
            timer_colour = settings.TIMER_WARNING
        else:
            timer_colour = settings.TEXT
        timer_text = fonts["timer"].render(self.time_loop.display_text(), True, timer_colour)
        # get_rect(midtop=...) positions the text by its top-centre point.
        timer_rect = timer_text.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 4))
        screen.blit(timer_text, timer_rect)
        loop_text = fonts["small"].render(f"Loop: {format_time(self.time_loop.duration)}",
                                          True, settings.DIM_TEXT)
        screen.blit(loop_text, loop_text.get_rect(midtop=(timer_rect.centerx, timer_rect.bottom)))

        # Left: the level name, plus the area when the level has several.
        name = self.level.name
        if len(self.level.areas) > 1:
            name += " - " + self.area_name.replace("_", " ").capitalize()
        level_text = fonts["small"].render(name, True, settings.TEXT)
        screen.blit(level_text, (16, 36))
        if self.can_race():
            hint = fonts["small"].render("C: race now", True, settings.DIM_TEXT)
            screen.blit(hint, (level_text.get_width() + 32, 36))

        # Right: the bag's slots, the parts counter beside them, and below,
        # the names of what's in the bag.
        right = settings.SCREEN_WIDTH - 16
        bag = self.player.bag
        slots_left = bag.draw_slots(screen, (right, 8))
        machine = self.level.machine
        counter = fonts["small"].render(f"Parts installed: {len(machine.installed)}/{machine.total_parts}",
                                        True, settings.TEXT)
        screen.blit(counter, counter.get_rect(topright=(slots_left - 16, 12)))
        if bag.items:
            names = ", ".join(item.name for item in bag.items)
        else:
            names = f"Bag: empty ({bag.capacity} slot{'s' if bag.capacity != 1 else ''})"
        bag_text = fonts["small"].render(names, True, settings.DIM_TEXT)
        screen.blit(bag_text, bag_text.get_rect(topright=(right, 36)))

    def draw_race_prompt(self, screen):
        fonts = self.game.fonts
        darken(screen)
        centre_x, centre_y = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
        title = fonts["big"].render("Race?", True, settings.HIGHLIGHT)
        screen.blit(title, title.get_rect(center=(centre_x, centre_y - 30)))
        lines = [f"Y: race, with {format_time(self.time_loop.time_left)} to finish a lap",
                 "N: stay in town until the loop ends"]
        for i, line in enumerate(lines):
            text = fonts["small"].render(line, True, settings.TEXT)
            screen.blit(text, text.get_rect(center=(centre_x, centre_y + 22 + i * 28)))

    def draw_cleared(self, screen):
        fonts = self.game.fonts
        darken(screen)
        centre_x, centre_y = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
        title = fonts["big"].render(f"{self.level.name} cleared!", True, settings.WIN)
        screen.blit(title, title.get_rect(center=(centre_x, centre_y - 30)))
        saved = fonts["small"].render("Sub-part built. Progress saved.", True, settings.TEXT)
        screen.blit(saved, saved.get_rect(center=(centre_x, centre_y + 22)))
        if self.next_level is not None:
            hint_text = f"Enter: continue to the {read_level_name(self.next_level)}     M: menu"
        else:
            hint_text = "Enter: back to the menu"
        hint = fonts["small"].render(hint_text, True, settings.TEXT)
        screen.blit(hint, hint.get_rect(center=(centre_x, centre_y + 50)))
        if self.can_race():
            race = fonts["small"].render("R: race for a time bonus first", True, settings.HIGHLIGHT)
            screen.blit(race, race.get_rect(center=(centre_x, centre_y + 78)))


# =====================================================================
#  RACING (Step 10: one lap against the clock; the rival comes in Step 11)
# =====================================================================

class RaceScene:
    RACING = "racing"
    WON = "won"          # crossed the line after every checkpoint, in time
    LOST = "lost"        # the race slot ran out, or the player gave up

    def __init__(self, game, return_to, track_id, slot):
        self.game = game
        self.return_to = return_to  # the paused LevelScene; we report back to it
        self.track_name, self.track, start_angle, self.checkpoints = load_track(track_id)
        self.car = Car(self.track.start_tile.center, start_angle)
        self.camera = Camera()

        # The race clock. The race slot is the time left in the loop, so
        # running out here means the loop is over.
        self.slot = slot
        self.time_left = slot
        # Index of the next checkpoint to drive through (0 = checkpoint 1).
        # When it equals len(self.checkpoints), the finish line counts.
        self.next_checkpoint = 0
        self.state = RaceScene.RACING
        self.bonus = 0
        self.new_best = False

        # Skid marks are drawn straight onto a copy of the track picture, so
        # they stay forever (for this visit) and cost nothing to redraw.
        self.track_picture = self.track.background.copy()
        # Dust puffs: each is [x, y, velocity_x, velocity_y, seconds_left].
        self.dust = []

    # ---------------- race rules ----------------

    def check_progress(self):
        """Checkpoints in order, then the finish line."""
        car_box = self.car.rect
        if self.next_checkpoint < len(self.checkpoints):
            # collidelist() gives the index of the first rect touched, or -1.
            if car_box.collidelist(self.checkpoints[self.next_checkpoint]) != -1:
                self.next_checkpoint += 1
        elif car_box.collidelist(self.track.finish_tiles) != -1:
            self.win()

    def win(self):
        # Design doc: bonus = the race slot + the time left in it at the finish.
        # A 32 s slot finished in 16 s earns 32 + 16 = 48 s.
        self.bonus = round(self.slot + self.time_left, 1)
        self.new_best = self.return_to.record_race_win(self.bonus)
        self.end(RaceScene.WON)

    def end(self, result):
        self.state = result
        self.game.tuning.close()  # so Enter goes to the result screen, not the panel

    # ---------------- the three scene methods ----------------

    def handle_event(self, event):
        # The live tuning panel gets first look at every key (see tuning.py).
        if self.game.tuning.handle_event(event):
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.state == RaceScene.RACING and event.key == pygame.K_ESCAPE:
            self.end(RaceScene.LOST)  # giving up counts as running out of time
        elif self.state != RaceScene.RACING and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.return_to.race_over(self.state == RaceScene.WON, self.bonus)

    def update(self, dt):
        throttle = brake = handbrake = False
        steer = 0
        if self.state == RaceScene.RACING:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.end(RaceScene.LOST)
            else:
                # Read the controls. key.get_pressed() says which keys are HELD now.
                keys = pygame.key.get_pressed()
                throttle = keys[pygame.K_w] or keys[pygame.K_UP]
                brake = keys[pygame.K_s] or keys[pygame.K_DOWN]
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    steer -= 1
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    steer += 1
                handbrake = keys[pygame.K_SPACE]
        # After the race the car keeps rolling with no input, so it coasts
        # to a stop behind the result screen instead of freezing.
        impact = self.car.update(dt, throttle, brake, steer, handbrake, self.track)
        if self.state == RaceScene.RACING:
            self.check_progress()

        # Game feel: the camera aims slightly AHEAD of the car (where it will be
        # in a moment), so you see more of the road you're driving towards.
        look_ahead = self.car.pos + self.car.velocity * settings.CAMERA_LOOKAHEAD
        self.camera.follow_smoothly(look_ahead, self.track.width, self.track.height, dt)

        # Game feel: shake the screen on hard hits, harder for faster hits.
        if impact > settings.SHAKE_MIN_IMPACT:
            self.camera.shake(min(settings.SHAKE_MAX, impact * settings.SHAKE_PER_SPEED))
        self.camera.update_shake(dt)

        # Game feel: skid marks and dust while sliding sideways.
        if abs(self.car.sideways_speed()) > settings.SKID_SPEED:
            self.leave_skid_marks()
        self.update_dust(dt)

    def leave_skid_marks(self):
        for wheel in self.car.rear_wheels():
            pygame.draw.circle(self.track_picture, settings.SKID_MARK, wheel, 2)
            if random.random() < 0.3:  # a puff now and then, not every frame
                drift = pygame.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
                self.dust.append([wheel.x, wheel.y, drift.x, drift.y, 0.6])

    def update_dust(self, dt):
        for puff in self.dust:
            puff[0] += puff[2] * dt
            puff[1] += puff[3] * dt
            puff[4] -= dt
        self.dust = [puff for puff in self.dust if puff[4] > 0]  # remove faded puffs

    def draw(self, screen):
        car, camera = self.car, self.camera
        screen.fill(settings.BACKGROUND)
        screen.blit(self.track_picture, camera.to_screen(self.track_picture.get_rect()))
        for x, y, _, _, life in self.dust:
            spot = camera.to_screen(pygame.Rect(round(x), round(y), 0, 0)).topleft
            pygame.draw.circle(screen, settings.DUST, spot, 2 + life * 6)  # shrinks as it fades
        car.draw(screen, camera)
        self.draw_hud(screen)
        if self.state != RaceScene.RACING:
            self.draw_result(screen)
        self.game.tuning.draw(screen, self.game.fonts)

    def draw_hud(self, screen):
        fonts = self.game.fonts
        pygame.draw.rect(screen, settings.HUD_BAR, (0, 0, settings.SCREEN_WIDTH, settings.HUD_HEIGHT))
        name = fonts["small"].render(self.track_name, True, settings.TEXT)
        screen.blit(name, (16, 36))

        # Centre: the race clock, red in the last few seconds, and what's next.
        colour = settings.TIMER_WARNING if self.time_left <= settings.WARNING_TIME else settings.TEXT
        clock = fonts["timer"].render(format_time(self.time_left), True, colour)
        clock_rect = clock.get_rect(midtop=(settings.SCREEN_WIDTH // 2, 4))
        screen.blit(clock, clock_rect)
        if self.next_checkpoint < len(self.checkpoints):
            goal = f"Checkpoint {self.next_checkpoint + 1} of {len(self.checkpoints)}"
        else:
            goal = "To the finish line!"
        goal_text = fonts["small"].render(goal, True, settings.DIM_TEXT)
        screen.blit(goal_text, goal_text.get_rect(midtop=(clock_rect.centerx, clock_rect.bottom)))

        # Right: the controls, and the speed under them.
        right = settings.SCREEN_WIDTH - 16
        hint = fonts["small"].render("WASD drive   Space drift   Tab tune   Esc give up",
                                     True, settings.DIM_TEXT)
        screen.blit(hint, hint.get_rect(topright=(right, 12)))
        # Total speed (length of the velocity), so sliding sideways still counts.
        speed = self.car.velocity.length() * settings.SPEED_DISPLAY_SCALE
        speed_text = fonts["small"].render(f"{speed:3.0f} km/h", True, settings.TEXT)
        screen.blit(speed_text, speed_text.get_rect(topright=(right, 36)))

    def draw_result(self, screen):
        fonts = self.game.fonts
        darken(screen)
        centre_x, centre_y = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
        after_clearing = (self.return_to.state == LevelScene.CLEARED)
        if self.state == RaceScene.WON:
            title, colour = "You won!", settings.WIN
            lap = self.slot - self.time_left
            lines = [f"Lap {lap:.1f} s.  Bonus: {self.slot:.1f} + {self.time_left:.1f} = {self.bonus:.1f} s"]
            if not self.return_to.bonus_counts:
                lines.append("Practice: this level is already cleared, so loops don't get longer")
            elif self.new_best:
                lines.append(f"New best! Loops here now last {format_time(self.return_to.loop_length())}")
            else:
                best = self.game.progress.best_bonus[self.return_to.level.id]
                lines.append(f"Your best is still {best:.1f} s, so loops don't get longer")
            if after_clearing:
                lines.append("Enter: back")
            else:
                lines.append(f"Enter: back to town with {format_time(self.bonus)} on the clock")
        else:
            title, colour = "Out of time!", settings.TIMER_WARNING
            if after_clearing:
                lines = ["No bonus this time.", "Enter: back"]
            else:
                lines = ["No bonus. The loop resets.", "Enter: back to the start of the loop"]
        title_text = fonts["big"].render(title, True, colour)
        screen.blit(title_text, title_text.get_rect(center=(centre_x, centre_y - 40)))
        for i, line in enumerate(lines):
            text = fonts["small"].render(line, True, settings.TEXT)
            screen.blit(text, text.get_rect(center=(centre_x, centre_y + 14 + i * 28)))
