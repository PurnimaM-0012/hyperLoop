# town.py
# The town map. For now it is just a list of walls: the outer boundary
# plus some grey blocks standing in for ruined buildings.

import pygame

import settings


class Town:
    def __init__(self):
        w, h, t = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, settings.WALL_THICKNESS

        # pygame.Rect(x, y, width, height). (0, 0) is the TOP-LEFT corner of
        # the window; x grows to the right and y grows DOWNWARD.
        self.walls = [
            # Outer boundary, so the player can't walk off the screen.
            pygame.Rect(0, 0, w, t),          # top
            pygame.Rect(0, h - t, w, t),      # bottom
            pygame.Rect(0, 0, t, h),          # left
            pygame.Rect(w - t, 0, t, h),      # right

            # Ruined buildings (placeholder layout).
            pygame.Rect(120, 100, 180, 120),
            pygame.Rect(420, 80, 120, 90),
            pygame.Rect(650, 110, 200, 140),
            pygame.Rect(100, 380, 140, 160),
            pygame.Rect(330, 420, 200, 100),
            pygame.Rect(640, 400, 90, 150),
            pygame.Rect(780, 420, 100, 120),
        ]

    def draw(self, screen):
        for wall in self.walls:
            pygame.draw.rect(screen, settings.WALL, wall)
