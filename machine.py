# machine.py
# The escape machine and the parts the player must bring to it.

import pygame

import settings


class Part:
    # The three states a part can be in. Each part is ALWAYS in exactly one.
    #   ON_GROUND --walk over it--> CARRIED --reach the machine--> INSTALLED
    # and the loop reset sends every part back to ON_GROUND.
    ON_GROUND = "on_ground"
    CARRIED = "carried"
    INSTALLED = "installed"

    # Bag item details (see bag.py): parts are loop items, so a loop reset
    # takes them out of the bag and sends them home.
    kind = "part"
    persistent = False

    def __init__(self, name, position, colour, area="main"):
        self.name = name
        self.home = position      # where it lies at the start of every loop (world coordinates)
        self.home_area = area     # ...and in which area (map) of the level
        self.colour = colour
        self.rect = pygame.Rect(0, 0, settings.PART_SIZE, settings.PART_SIZE)
        self.reset()

    def reset(self):
        """Put the part back on the ground at its starting position."""
        self.state = Part.ON_GROUND
        self.area = self.home_area
        self.rect.topleft = self.home
        # True right after the player drops it: until they step away it
        # neither blocks them nor gets picked straight back up.
        self.just_dropped = False

    def drop_at(self, centre, area):
        """Put the part on the ground, centred on a point, in an area."""
        self.state = Part.ON_GROUND
        self.area = area
        self.rect.center = centre
        self.just_dropped = True

    def draw(self, screen, camera):
        # Only parts on the ground are drawn here. Carried parts are drawn
        # above the player, and installed parts inside the machine.
        if self.state == Part.ON_GROUND:
            pygame.draw.rect(screen, self.colour, camera.to_screen(self.rect))

    def draw_at(self, screen, center):
        """Draw the part centred on a point (used above the player's head)."""
        rect = self.rect.copy()
        rect.center = center
        pygame.draw.rect(screen, self.colour, rect)


class Machine:
    def __init__(self, rect, total_parts):
        self.rect = pygame.Rect(rect)
        self.total_parts = total_parts
        self.installed = []  # the parts installed so far, in order

    def reset(self):
        """Empty the machine (used when a loop resets)."""
        self.installed = []

    def install(self, part):
        part.state = Part.INSTALLED
        self.installed.append(part)

    def is_complete(self):
        return len(self.installed) == self.total_parts

    def draw(self, screen, camera, built_subparts=0):
        """Draw the machine. built_subparts = sub-parts from cleared levels."""
        rect = camera.to_screen(self.rect)  # where the machine is in the window

        # The machine's outline (width=2 draws just the border, not filled).
        pygame.draw.rect(screen, settings.MACHINE, rect, width=2)

        # Sub-parts built in earlier levels: small green blocks along the top
        # edge. They are PERSISTENT, so the loop reset never removes them.
        for i in range(built_subparts):
            block = pygame.Rect(rect.left + 4 + i * 14, rect.top - 12, 10, 8)
            pygame.draw.rect(screen, settings.WIN, block)

        # One slot per part of THIS level, spread evenly across the machine.
        # A slot is filled with the colour of the part installed in it.
        slot_size = settings.PART_SIZE
        gap = (rect.width - self.total_parts * slot_size) // (self.total_parts + 1)
        for i in range(self.total_parts):
            slot = pygame.Rect(0, 0, slot_size, slot_size)
            slot.left = rect.left + gap + i * (slot_size + gap)
            slot.centery = rect.centery
            if i < len(self.installed):
                pygame.draw.rect(screen, self.installed[i].colour, slot)
            else:
                pygame.draw.rect(screen, settings.EMPTY_SLOT, slot)
