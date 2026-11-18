# camera.py
# Lets a map be bigger than the window. Things in the game have WORLD
# coordinates (their position on the map). The camera is a window-sized
# rectangle that moves around the world, following the player. To draw
# something, we turn its world position into a SCREEN position by
# subtracting the camera's position.

import settings


class Camera:
    def __init__(self):
        # The part of the window the map is shown in (below the HUD bar).
        self.view_width = settings.SCREEN_WIDTH
        self.view_height = settings.SCREEN_HEIGHT - settings.HUD_HEIGHT
        # The camera's top-left corner, in world coordinates.
        self.x = 0
        self.y = 0

    def follow(self, target_rect, world_width, world_height):
        """Centre the camera on the target, without showing past the map's edges."""
        self.x = self.position_on_axis(target_rect.centerx, self.view_width, world_width)
        self.y = self.position_on_axis(target_rect.centery, self.view_height, world_height)

    @staticmethod
    def position_on_axis(target_centre, view_size, world_size):
        # A map smaller than the view: centre it. The result is negative,
        # which pushes the map towards the middle of the window.
        if world_size <= view_size:
            return (world_size - view_size) // 2
        # Otherwise put the target in the middle of the view...
        position = target_centre - view_size // 2
        # ...but CLAMP it: never left of / above the map, never past its far edge.
        return max(0, min(position, world_size - view_size))

    def to_screen(self, rect):
        """A world rect -> where to draw it in the window (a moved copy).

        The map is drawn below the HUD bar, so we also shift down by HUD_HEIGHT.
        """
        return rect.move(-self.x, settings.HUD_HEIGHT - self.y)
