# bag.py
# The player's bag: a limited number of slots shared by EVERYTHING you can
# carry. Today that's machine parts; later utilities, fuel and scrap go in
# the same bag, which is what forces the player to choose what to take.
#
# Every item has a 'kind' ("part" now; "utility", "fuel", "scrap" later)
# and a 'persistent' flag: persistent items survive a loop reset, the rest
# are emptied out of the bag when the loop resets.

import pygame

import settings


class Bag:
    def __init__(self, capacity):
        self.capacity = capacity  # how many slots (grows with progress)
        self.items = []           # what's in the bag, oldest first

    def has_room(self):
        return len(self.items) < self.capacity

    def add(self, item):
        self.items.append(item)

    def remove(self, item):
        self.items.remove(item)

    def take_last(self):
        """Remove and return the most recently added item (for dropping)."""
        return self.items.pop()

    def parts(self):
        """Just the machine parts in the bag (the machine only accepts these)."""
        return [item for item in self.items if item.kind == "part"]

    def empty_for_new_loop(self):
        """Loop reset: keep persistent items (utilities, later), lose the rest."""
        self.items = [item for item in self.items if item.persistent]

    def draw_slots(self, screen, top_right):
        """Draw one box per slot, ending at top_right; filled slots show the
        item's colour. Returns the left edge, so other HUD text can go beside it."""
        size, gap = settings.BAG_SLOT_SIZE, 6
        width = self.capacity * size + (self.capacity - 1) * gap
        left = top_right[0] - width
        for i in range(self.capacity):
            slot = pygame.Rect(left + i * (size + gap), top_right[1], size, size)
            if i < len(self.items):
                pygame.draw.rect(screen, self.items[i].colour, slot.inflate(-6, -6))
            pygame.draw.rect(screen, settings.DIM_TEXT, slot, width=1)
        return left
