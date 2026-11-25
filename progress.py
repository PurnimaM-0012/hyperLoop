# progress.py
# Everything that SURVIVES a loop reset. reset_loop() in main.py never
# touches this object; only specific events change it (clearing a level,
# winning a race, picking up a utility).
#
# It can be saved to a JSON file, so progress also survives closing the game.

import json
import os

import settings

SAVE_VERSION = 2  # bump this if the save format ever changes (2: best_bonus per level)


class Progress:
    def __init__(self):
        self.new_game()

    def new_game(self):
        """Wipe everything back to the start of a brand-new game."""
        self.current_level = settings.LEVEL_ORDER[0]      # the level being played
        self.cleared_levels = []    # levels whose sub-part is built, in order
        self.bag_capacity = settings.START_BAG_CAPACITY
        self.utilities = []         # utilities owned (Step 13)
        # Each level's BEST race bonus in seconds, e.g. {"prison": 34}.
        # We keep only the best, never a running total, so bonuses don't
        # stack: racing again only helps if you beat your best.
        self.best_bonus = {}

    # ---------------- Loop length ----------------

    def loop_length(self, level_id, loop_cap):
        """How long a loop lasts in this level, in seconds.

        Rule (design doc): 80 s + the best race bonuses of this level and
        every level BEFORE it, capped at this level's maximum.
        It is worked out fresh from best_bonus every time, never stored,
        so it can't drift out of step with the rule. That also makes
        replays fair: later levels' bonuses aren't counted.
        """
        index = settings.LEVEL_ORDER.index(level_id)
        levels_so_far = settings.LEVEL_ORDER[:index + 1]  # this level and earlier ones
        bonuses = sum(self.best_bonus.get(lid, 0) for lid in levels_so_far)
        return min(settings.START_LOOP_DURATION + bonuses, loop_cap)

    # ---------------- Changing progress ----------------

    def record_race_win(self, level_id, bonus):
        """Remember a race win. Returns True if it beat the level's best."""
        if bonus > self.best_bonus.get(level_id, 0):
            self.best_bonus[level_id] = bonus
            return True
        return False

    def clear_level(self, level_id):
        """Record that a level's sub-part is built, and move to the next level."""
        if level_id not in self.cleared_levels:
            self.cleared_levels.append(level_id)
            # Each level cleared for the FIRST time adds a bag slot.
            # (Rule from the design doc; subject to change.)
            self.bag_capacity += settings.BAG_SLOTS_PER_LEVEL
        # Advance to the next level in the fixed order, if there is one.
        # Only when clearing the CURRENT level: replaying an earlier level
        # must never move you backwards.
        if level_id == self.current_level:
            index = settings.LEVEL_ORDER.index(level_id)
            if index + 1 < len(settings.LEVEL_ORDER):
                self.current_level = settings.LEVEL_ORDER[index + 1]

    # ---------------- Saving and loading ----------------
    # JSON is a plain-text format for numbers, text, lists and dictionaries.
    # Open save.json in VS Code to see exactly what the game remembers.

    def to_dict(self):
        return {
            "version": SAVE_VERSION,
            "current_level": self.current_level,
            "cleared_levels": self.cleared_levels,
            "bag_capacity": self.bag_capacity,
            "utilities": self.utilities,
            "best_bonus": self.best_bonus,
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
            progress.current_level = data.get("current_level", progress.current_level)
            progress.cleared_levels = data.get("cleared_levels", [])
            progress.bag_capacity = data.get("bag_capacity", progress.bag_capacity)
            progress.utilities = data.get("utilities", [])
            # Saves before Step 10 stored one running "loop_duration" instead.
            # It's ignored: loop length is now worked out from best_bonus.
            progress.best_bonus = data.get("best_bonus", {})
            # Saves made before Step 8 cleared levels without growing the
            # bag. Make sure the bag is at least as big as the rule says.
            # (Fixing up old saves like this is called a "migration".)
            earned = settings.START_BAG_CAPACITY + settings.BAG_SLOTS_PER_LEVEL * len(progress.cleared_levels)
            progress.bag_capacity = max(progress.bag_capacity, earned)
        except (OSError, ValueError):
            # The file couldn't be read or isn't valid JSON: start fresh
            # rather than crash. (ValueError covers broken JSON.)
            return cls(), False
        return progress, True
