# tuning.py
# A live tuning panel for the car. It changes the numbers in settings.py
# WHILE you drive: the car reads settings.CAR_... every frame, so a change
# takes effect immediately. Nothing is written to settings.py itself; press
# F6 to save the current values to tuning.txt, then copy the ones you like.
#
# Keys (on the race track):
#   Tab        show / hide the panel
#   [ and ]    choose the previous / next setting
#   - and =    lower / raise the chosen setting (hold to repeat)
#   Backspace  put the chosen setting back to its starting value
#   F6         save all values to tuning.txt

import os

import pygame

import settings

# (setting name in settings.py, how much one key press changes it, short description)
TUNABLE = [
    ("CAR_MAX_SPEED", 20, "top speed on road"),
    ("CAR_ACCELERATION", 20, "how quickly you speed up"),
    ("CAR_BRAKE", 50, "braking strength"),
    ("CAR_DRAG", 0.1, "slowing down when you let go"),
    ("CAR_TURN_RATE", 5, "turning speed (degrees/s)"),
    ("CAR_STEER_RESPONSE", 0.5, "how fast steering builds up"),
    ("CAR_HIGH_SPEED_STEER", 0.05, "share of turning left at top speed"),
    ("CAR_GRIP", 0.5, "resistance to sliding sideways"),
    ("CAR_HANDBRAKE_GRIP", 0.1, "grip while drifting (Space)"),
    ("CAR_HANDBRAKE_STEER", 0.05, "extra turning while drifting"),
    ("CAR_HANDBRAKE_DRAG", 0.1, "speed lost while drifting"),
    ("CAR_BOUNCE", 0.05, "speed kept when hitting a barrier"),
    ("OFFROAD_DRAG", 0.1, "extra slowing on grass"),
    ("OFFROAD_SLOWDOWN", 0.25, "how fast speed drops entering grass"),
    ("CAMERA_LOOKAHEAD", 0.05, "how far ahead the camera looks (s)"),
    ("CAMERA_SMOOTHING", 0.5, "how quickly the camera catches up"),
]

TUNING_FILE = os.path.join(settings.BASE_DIR, "tuning.txt")


def show(value):
    """Whole numbers without decimals, small numbers with two."""
    return f"{value:.0f}" if value >= 10 else f"{value:.2f}"


class TuningPanel:
    def __init__(self):
        self.visible = False
        self.selected = 0
        # Remember the values the game started with, for Backspace and for
        # showing what changed. getattr(settings, "X") reads settings.X.
        self.original = {name: getattr(settings, name) for name, _, _ in TUNABLE}
        self.message = ""

    def handle_event(self, event):
        """Handle a key press. Returns True if the panel used it."""
        if event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_TAB:
            self.visible = not self.visible
            # Key repeat: while the panel is open, holding - or = keeps
            # changing the value. Turned off again when the panel closes.
            pygame.key.set_repeat(300, 50) if self.visible else pygame.key.set_repeat(0)
            return True
        if not self.visible:
            return False

        name, step, _ = TUNABLE[self.selected]
        if event.key == pygame.K_RIGHTBRACKET:
            self.selected = (self.selected + 1) % len(TUNABLE)
        elif event.key == pygame.K_LEFTBRACKET:
            self.selected = (self.selected - 1) % len(TUNABLE)
        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.change(name, step)
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.change(name, -step)
        elif event.key == pygame.K_BACKSPACE:
            setattr(settings, name, self.original[name])
        elif event.key == pygame.K_F6:
            self.save()
        else:
            return False
        return True

    def change(self, name, amount):
        # setattr(settings, "X", v) does settings.X = v. round() stops tiny
        # decimal errors building up (0.1 + 0.2 is 0.30000000000000004).
        value = round(getattr(settings, name) + amount, 4)
        setattr(settings, name, max(0, value))

    def close(self):
        """Call when leaving the track, so key repeat doesn't stay on."""
        self.visible = False
        pygame.key.set_repeat(0)

    def save(self):
        lines = ["# Car tuning saved from the live tuning panel.",
                 "# Copy the lines you like into settings.py.", ""]
        for name, _, description in TUNABLE:
            value, was = getattr(settings, name), self.original[name]
            note = f"  # {description}" + ("" if value == was else f" (was {show(was)})")
            lines.append(f"{name} = {value}{note}")
        with open(TUNING_FILE, "w") as file:
            file.write("\n".join(lines) + "\n")
        self.message = "Saved to tuning.txt"

    def draw(self, screen, fonts):
        if not self.visible:
            return
        font = fonts["small"]
        row_height = 22
        # On the right of the screen, so it covers less of the road at the start.
        width = 430
        panel = pygame.Rect(settings.SCREEN_WIDTH - width - 12, settings.HUD_HEIGHT + 12,
                            width, 64 + row_height * len(TUNABLE))
        # A see-through dark box so the track still shows behind it.
        box = pygame.Surface(panel.size, pygame.SRCALPHA)
        box.fill((0, 0, 0, 190))
        screen.blit(box, panel.topleft)

        y = panel.top + 10
        title = font.render("LIVE TUNING   [ ] choose   - = change", True, settings.TEXT)
        screen.blit(title, (panel.left + 12, y))
        y += row_height + 6
        for i, (name, _, _) in enumerate(TUNABLE):
            value = getattr(settings, name)
            changed = value != self.original[name]
            if i == self.selected:
                colour = settings.HIGHLIGHT
            elif changed:
                colour = settings.TEXT
            else:
                colour = settings.DIM_TEXT
            marker = ">" if i == self.selected else " "
            label = font.render(f"{marker} {name}", True, colour)
            screen.blit(label, (panel.left + 12, y))
            text = show(value) + ("  *" if changed else "")
            number = font.render(text, True, colour)
            screen.blit(number, number.get_rect(topright=(panel.right - 12, y)))
            y += row_height

        _, _, description = TUNABLE[self.selected]
        footer = self.message or f"{description}   (Backspace reset, F6 save)"
        hint = font.render(footer, True, settings.DIM_TEXT)
        screen.blit(hint, (panel.left + 12, y + 4))
