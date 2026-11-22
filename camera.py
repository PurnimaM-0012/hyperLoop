# camera.py
# Lets a map be bigger than the window. Things in the game have WORLD
# coordinates (their position on the map). The camera is a window-sized
# rectangle that moves around the world, following the player. To draw
# something, we turn its world position into a SCREEN position by
# subtracting the camera's position.

import math
import random

import settings


class Camera:
    def __init__(self):
        # The part of the window the map is shown in (below the HUD bar).
        self.view_width = settings.SCREEN_WIDTH
        self.view_height = settings.SCREEN_HEIGHT - settings.HUD_HEIGHT
        # The camera's top-left corner, in world coordinates.
        self.x = 0
        self.y = 0
        # Exact (decimal) position, used by smooth following.
        self.exact_x = None
        self.exact_y = None
        # Screen shake: how strong it is now (pixels), and this frame's offset.
        self.shake_strength = 0
        self.shake_offset = (0, 0)

    def follow(self, target_rect, world_width, world_height):
        """Centre the camera on the target, without showing past the map's edges."""
        self.x = self.position_on_axis(target_rect.centerx, self.view_width, world_width)
        self.y = self.position_on_axis(target_rect.centery, self.view_height, world_height)

    def follow_smoothly(self, point, world_width, world_height, dt):
        """Glide towards centring 'point', instead of jumping there at once.

        Each frame we close part of the gap to where the camera wants to be.
        1 - exp(-smoothing * dt) is the part to close: it depends on dt, so
        the camera glides at the same speed at any frame rate.
        """
        target_x = self.position_on_axis(point[0], self.view_width, world_width)
        target_y = self.position_on_axis(point[1], self.view_height, world_height)
        if self.exact_x is None:              # first frame: jump straight there
            self.exact_x, self.exact_y = target_x, target_y
        blend = 1 - math.exp(-settings.CAMERA_SMOOTHING * dt)
        self.exact_x += (target_x - self.exact_x) * blend
        self.exact_y += (target_y - self.exact_y) * blend
        self.x, self.y = round(self.exact_x), round(self.exact_y)

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

    # ---------------- screen shake ----------------

    def shake(self, strength):
        """Start shaking (a stronger hit replaces a weaker shake)."""
        self.shake_strength = max(self.shake_strength, strength)

    def update_shake(self, dt):
        """Pick a random offset this frame, and let the shake fade away."""
        if self.shake_strength > 0:
            s = self.shake_strength
            self.shake_offset = (round(random.uniform(-s, s)), round(random.uniform(-s, s)))
            self.shake_strength = max(0, s - settings.SHAKE_DECAY * dt)
        else:
            self.shake_offset = (0, 0)

    def to_screen(self, rect):
        """A world rect -> where to draw it in the window (a moved copy).

        The map is drawn below the HUD bar, so we also shift down by HUD_HEIGHT.
        Screen shake just nudges everything by a small random offset.
        """
        return rect.move(-self.x + self.shake_offset[0],
                         settings.HUD_HEIGHT - self.y + self.shake_offset[1])
