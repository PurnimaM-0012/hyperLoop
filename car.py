# car.py
# A top-down arcade car. Unlike the player (who moves exactly where the keys
# say), a car has:
#   - an ANGLE: which way it points (0 = right, 90 = down, in degrees)
#   - a VELOCITY: where it's actually going, which is NOT always where it points
# The gap between the two is what makes sliding and drifting possible.

import math

import pygame

import settings


def fade(value, rate, dt):
    """Shrink 'value' towards 0 at 'rate' per second, the same at any frame rate.

    Multiplying by a fixed number each frame (say 0.9) would fade faster at
    120 FPS than at 60 FPS. math.exp(-rate * dt) gives the same fade per
    SECOND no matter how many frames that second is split into.
    """
    return value * math.exp(-rate * dt)


class Car:
    def __init__(self, start_centre, start_angle):
        self.pos = pygame.Vector2(start_centre)  # centre of the car, world coordinates
        self.angle = start_angle                 # degrees
        self.velocity = pygame.Vector2(0, 0)     # pixels per second
        # How far the "steering wheel" is turned: -1 (full left) to 1 (full
        # right). Keys are on/off, so instead of jumping to full lock we
        # move this towards the key's value a little each frame.
        self.steering = 0.0
        self.rect = pygame.Rect(0, 0, settings.CAR_HITBOX, settings.CAR_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # The car's picture, drawn once pointing right (angle 0). Each frame
        # we rotate a copy. SRCALPHA keeps the corners see-through when rotated.
        self.image = pygame.Surface((settings.CAR_LENGTH, settings.CAR_WIDTH), pygame.SRCALPHA)
        self.image.fill(settings.CAR_BODY)
        front = pygame.Rect(settings.CAR_LENGTH - 9, 0, 9, settings.CAR_WIDTH)
        pygame.draw.rect(self.image, settings.CAR_FRONT, front)

    # ---------------- directions ----------------

    def forward(self):
        """A length-1 vector pointing where the car faces.

        Vector2(1, 0) points right; rotate() turns it by the car's angle.
        (This is the same as (cos(angle), sin(angle)).)
        """
        return pygame.Vector2(1, 0).rotate(self.angle)

    def right(self):
        """A length-1 vector pointing out of the car's right side."""
        return pygame.Vector2(1, 0).rotate(self.angle + 90)

    def forward_speed(self):
        """How fast the car moves the way it faces (negative = reversing).

        The DOT PRODUCT of the velocity with a length-1 direction gives how
        much of the velocity goes in that direction.
        """
        return self.velocity.dot(self.forward())

    def sideways_speed(self):
        """How fast the car slides sideways. Big = drifting."""
        return self.velocity.dot(self.right())

    # ---------------- driving ----------------

    def update(self, dt, throttle, brake, steer, handbrake, area):
        """Drive for dt seconds.

        throttle, brake, handbrake: True/False.  steer: the keys, -1 (left), 0, or 1 (right).
        area: the track, for barriers and tile speeds.
        Returns how hard the car hit a barrier this frame (0 = no hit).
        """
        speed = self.forward_speed()

        # --- 1. Steering.
        # (a) Ease the steering wheel towards the key's value (-1, 0 or 1),
        # by at most CAR_STEER_RESPONSE per second. A quick tap then only
        # turns the wheel a little, which makes small corrections possible.
        step = settings.CAR_STEER_RESPONSE * dt
        if self.steering < steer:
            self.steering = min(steer, self.steering + step)
        elif self.steering > steer:
            self.steering = max(steer, self.steering - step)
        # (b) Weaker at low speed (a parked car can't spin)...
        steer_strength = min(1, abs(speed) / settings.CAR_FULL_STEER_SPEED)
        # (c) ...and calmer at high speed: full turn rate when slow, down to
        # CAR_HIGH_SPEED_STEER of it at top speed.
        speed_share = min(1, abs(speed) / settings.CAR_MAX_SPEED)
        steer_strength *= 1 - (1 - settings.CAR_HIGH_SPEED_STEER) * speed_share
        # (d) Reversed when going backwards, like a real car.
        direction = 1 if speed >= 0 else -1
        turn = settings.CAR_TURN_RATE * self.steering * steer_strength * direction * dt
        if handbrake:
            turn *= settings.CAR_HANDBRAKE_STEER
        self.angle = (self.angle + turn) % 360

        # --- 2. Split the velocity into forward and sideways parts, using
        # the NEW facing direction. Turning doesn't change the velocity, so
        # after a turn some of it is now "sideways": the car starts to slide.
        forward, right = self.forward(), self.right()
        forward_part = self.velocity.dot(forward)
        sideways_part = self.velocity.dot(right)

        # --- 3. Throttle, brake and reverse act along the forward direction.
        if throttle:
            forward_part += settings.CAR_ACCELERATION * dt
        if brake:
            if forward_part > 5:
                # Moving forwards: brake, but never past a standstill.
                forward_part = max(0, forward_part - settings.CAR_BRAKE * dt)
            else:
                forward_part -= settings.CAR_REVERSE_ACCELERATION * dt

        # --- 4. Friction. Rolling resistance always; more on grass; more
        # with the handbrake on.
        terrain = area.speed_at(self.pos)          # 1 on road, 0.5 on grass
        drag = settings.CAR_DRAG
        if terrain < 1:
            drag += settings.OFFROAD_DRAG
        if handbrake:
            drag += settings.CAR_HANDBRAKE_DRAG
        forward_part = fade(forward_part, drag, dt)

        # --- 5. GRIP: tyres fight sideways sliding. Normally they cancel it
        # quickly; with the handbrake they barely do, so the car DRIFTS.
        grip = settings.CAR_HANDBRAKE_GRIP if handbrake else settings.CAR_GRIP
        sideways_part = fade(sideways_part, grip, dt)

        # --- 6. Speed limits (lower on slow tiles like grass).
        top = settings.CAR_MAX_SPEED * terrain
        forward_part = max(-settings.CAR_REVERSE_MAX_SPEED, min(forward_part, top))

        # Put the two parts back together.
        self.velocity = forward * forward_part + right * sideways_part

        # --- 7. Move, bouncing off barriers.
        return self.move(dt, area.walls)

    def move(self, dt, walls):
        """Move by velocity * dt, one axis at a time (like the player), but
        BOUNCE off barriers instead of just stopping. Returns the impact speed."""
        impact = 0

        self.pos.x += self.velocity.x * dt
        self.rect.centerx = round(self.pos.x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.velocity.x > 0:
                    self.rect.right = wall.left
                else:
                    self.rect.left = wall.right
                self.pos.x = self.rect.centerx
                impact = max(impact, abs(self.velocity.x))
                self.velocity.x = -self.velocity.x * settings.CAR_BOUNCE

        self.pos.y += self.velocity.y * dt
        self.rect.centery = round(self.pos.y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.velocity.y > 0:
                    self.rect.bottom = wall.top
                else:
                    self.rect.top = wall.bottom
                self.pos.y = self.rect.centery
                impact = max(impact, abs(self.velocity.y))
                self.velocity.y = -self.velocity.y * settings.CAR_BOUNCE

        return impact

    def rear_wheels(self):
        """World positions of the two rear wheels (where skid marks appear)."""
        back = self.pos - self.forward() * (settings.CAR_LENGTH / 2 - 4)
        side = self.right() * (settings.CAR_WIDTH / 2 - 3)
        return back + side, back - side

    # ---------------- drawing ----------------

    def draw(self, screen, camera):
        # pygame.transform.rotate turns ANTI-clockwise for positive angles,
        # but our angles turn clockwise on screen (y grows downward), so we
        # rotate by -angle. A rotated image is bigger than the original, so we
        # re-centre it on the car's position.
        rotated = pygame.transform.rotate(self.image, -self.angle)
        centre = camera.to_screen(pygame.Rect(round(self.pos.x), round(self.pos.y), 0, 0)).topleft
        screen.blit(rotated, rotated.get_rect(center=centre))
