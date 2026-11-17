# progress.py
# Everything that SURVIVES a loop reset. reset_loop() in main.py never
# touches this object; only specific events change it (clearing a level,
# winning a race, picking up a utility).
#
# It can be saved to a JSON file, so progress also survives closing the game.

import json
import os

import settings

SAVE_VERSION = 1  # bump this if the save format ever changes


class Progress:
    def __init__(self):
        self.new_game()

    def new_game(self):
        """Wipe everything back to the start of a brand-new game."""
        self.loop_duration = settings.START_LOOP_DURATION  # seconds per loop
        self.current_level = settings.LEVEL_ORDER[0]      # the level being played
        self.cleared_levels = []    # levels whose sub-part is built, in order
        self.bag_capacity = settings.START_BAG_CAPACITY
        self.utilities = []         # utilities owned (Step 13)
        self.races_won = []         # races already won once (Step 10)

    # ---------------- Changing progress ----------------

    def add_loop_time(self, seconds):
        """Make every FUTURE loop longer (race wins call this)."""
        self.loop_duration += seconds

    def clear_level(self, level_id):
        """Record that a level's sub-part is built, and move to the next level."""
        if level_id not in self.cleared_levels:
            self.cleared_levels.append(level_id)
        # Advance to the next level in the fixed order, if there is one.
        index = settings.LEVEL_ORDER.index(level_id)
        if index + 1 < len(settings.LEVEL_ORDER):
            self.current_level = settings.LEVEL_ORDER[index + 1]

    # ---------------- Saving and loading ----------------
    # JSON is a plain-text format for numbers, text, lists and dictionaries.
    # Open save.json in VS Code to see exactly what the game remembers.

    def to_dict(self):
        return {
            "version": SAVE_VERSION,
            "loop_duration": self.loop_duration,
            "current_level": self.current_level,
            "cleared_levels": self.cleared_levels,
            "bag_capacity": self.bag_capacity,
            "utilities": self.utilities,
            "races_won": self.races_won,
        }

    def save(self, path):
        with open(path, "w") as file:
            json.dump(self.to_dict(), file, indent=2)  # indent = easy to read

    @classmethod
    def load(cls, path):
        """Return (progress, loaded). Starts a new game if there's no usable save.

        A 'classmethod' is called on the class itself, Progress.load(...),
        because it CREATES a Progress rather than changing an existing one.
        """
        progress = cls()
        if not os.path.exists(path):
            return progress, False
        try:
            with open(path) as file:
                data = json.load(file)
            # .get(key, default) keeps the new-game value if a key is missing,
            # so an older or hand-edited save file can't crash the game.
            progress.loop_duration = data.get("loop_duration", progress.loop_duration)
            progress.current_level = data.get("current_level", progress.current_level)
            progress.cleared_levels = data.get("cleared_levels", [])
            progress.bag_capacity = data.get("bag_capacity", progress.bag_capacity)
            progress.utilities = data.get("utilities", [])
            progress.races_won = data.get("races_won", [])
        except (OSError, ValueError):
            # The file couldn't be read or isn't valid JSON: start fresh
            # rather than crash. (ValueError covers broken JSON.)
            return cls(), False
        return progress, True
