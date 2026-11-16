# player.py
# The player: reads the keyboard, moves at a fixed speed, and stops at walls.

import pygame

import settings


class Player:
    def __init__(self, start):
        # 'pos' stores the exact position as decimals (e.g. 480.37).
        # 'rect' is the whole-pixel box used for drawing and collisions.
        # We need both: at 200 px/s one frame moves about 3.3 px, and a Rect
        # would throw away the .3 every frame, making movement uneven.
        self.pos = pygame.Vector2(start)
        self.rect = pygame.Rect(0, 0, settings.PLAYER_SIZE, settings.PLAYER_SIZE)
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))

    def read_input(self):
        """Turn the keys being held down into a direction, like (1, 0) for right."""
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1  # up is NEGATIVE y, because y grows downward
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        # Holding right + down gives (1, 1), which is about 1.41 long, so
        # diagonal movement would be 41% faster. normalize() shrinks it to
        # length 1 while keeping its direction.
        if direction.length() > 0:
            direction = direction.normalize()
        return direction

    def update(self, dt, walls):
        self.move(self.read_input(), dt, walls)

    def move(self, direction, dt, walls):
        """Move in 'direction' for 'dt' seconds without entering any wall."""
        step = direction * settings.PLAYER_SPEED * dt

        # Move and fix collisions ONE AXIS AT A TIME. If we moved diagonally
        # into a wall in one go, we couldn't tell which side we hit. Doing x
        # then y lets the player slide along a wall instead of sticking to it.

        # --- Left / right ---
        self.pos.x += step.x
        self.rect.x = round(self.pos.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if step.x > 0:                    # moving right: hit wall's left side
                    self.rect.right = wall.left
                elif step.x < 0:                  # moving left: hit wall's right side
                    self.rect.left = wall.right
                self.pos.x = self.rect.x          # keep exact position in sync

        # --- Up / down ---
        self.pos.y += step.y
        self.rect.y = round(self.pos.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if step.y > 0:                    # moving down: hit wall's top
                    self.rect.bottom = wall.top
                elif step.y < 0:                  # moving up: hit wall's bottom
                    self.rect.top = wall.bottom
                self.pos.y = self.rect.y

    def draw(self, screen):
        pygame.draw.rect(screen, settings.PLAYER, self.rect)
