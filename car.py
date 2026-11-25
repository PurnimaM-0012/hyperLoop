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


def car_picture(body_colour, front_colour):
    """The car drawn once, pointing right (angle 0). Each frame we rotate a
    copy. SRCALPHA keeps the corners see-through when rotated."""
    image = pygame.Surface((settings.CAR_LENGTH, settings.CAR_WIDTH), pygame.SRCALPHA)
    image.fill(body_colour)
    front = pygame.Rect(settings.CAR_LENGTH - 9, 0, 9, settings.CAR_WIDTH)
    pygame.draw.rect(image, front_colour, front)
    return image


class Car:
    def __init__(self, start_centre, start_angle, body_colour=None, front_colour=None):
        self.pos = pygame.Vector2(start_centre)  # centre of the car, world coordinates
        self.angle = start_angle                 # degrees
        self.velocity = pygame.Vector2(0, 0)     # pixels per second
        # How far the "steering wheel" is turned: -1 (full left) to 1 (full
        # right). Keys are on/off, so instead of jumping to full lock we
        # move this towards the key's value a little each frame.
        self.steering = 0.0
        self.rect = pygame.Rect(0, 0, settings.CAR_HITBOX, settings.CAR_HITBOX)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # Health (Step 11). Every car starts each race with full health;
        # hits take it away, and at 0 the car is wrecked.
        self.health = settings.CAR_HEALTH
        # Multiplies the top speed. 1 = normal. The rival's rubber band
        # changes it (rival.py); the player's car always keeps 1.
        self.speed_factor = 1.0

        # Every car has the same handling (settings.CAR_...); only the
        # colour differs. Later, car models will have their own settings.
        self.image = car_picture(body_colour or settings.CAR_BODY,
                                 front_colour or settings.CAR_FRONT)

    # ---------------- health ----------------

    @property
    def wrecked(self):
        return self.health <= 0

    def health_share(self):
        """Health left as a share of full: 1 = full, 0.5 = half, 0 = wrecked."""
        return self.health / settings.CAR_HEALTH

    def take_damage(self, impact):
        """Lose health from a hit at 'impact' speed (pixels per second).

        Light taps cost nothing. Above that, harder hits cost more: a hit at
        full road speed costs CAR_FULL_HIT_DAMAGE (25 of the 100 health),
        never more. Returns the damage taken.
        """
        if self.wrecked or impact < settings.CAR_DAMAGE_MIN_IMPACT:
            return 0
        damage = min(settings.CAR_FULL_HIT_DAMAGE,
                     settings.CAR_FULL_HIT_DAMAGE * impact / settings.CAR_MAX_SPEED)
        self.health = max(0, self.health - damage)
        if self.wrecked:
            # A wreck stops dead and turns grey. It stays on the track as an obstacle.
            self.velocity = pygame.Vector2(0, 0)
            self.image = car_picture(settings.WRECK_BODY, settings.WRECK_FRONT)
        return damage

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
        top = settings.CAR_MAX_SPEED * terrain * self.speed_factor
        if forward_part > top and terrain < 1:
            # Driving onto grass: bleed off the extra speed over a moment,
            # instead of cutting it instantly (which feels like hitting a wall).
            forward_part = top + fade(forward_part - top, settings.OFFROAD_SLOWDOWN, dt)
        else:
            forward_part = min(forward_part, top)
        forward_part = max(-settings.CAR_REVERSE_MAX_SPEED, forward_part)

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

    def sync_rect(self):
        """Put the collision box back on the car after pos changed."""
        self.rect.center = (round(self.pos.x), round(self.pos.y))

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


# ---------------- car-to-car crashes ----------------

def bump_cars(a, b):
    """If cars a and b overlap, push them apart and bounce them off each other.

    For this test each car counts as a CIRCLE: two circles touch when the
    distance between their centres is less than the two radii added up.
    That is much simpler than testing two rotated rectangles.
    Returns the crash speed (how fast they were closing in), 0 for no crash.
    A wreck doesn't move: it acts like a barrier for the other car.
    """
    if a.wrecked and b.wrecked:
        return 0
    offset = b.pos - a.pos
    distance = offset.length()
    touching = 2 * settings.CAR_CRASH_RADIUS
    if distance >= touching or distance == 0:
        return 0

    # 'normal' is the length-1 direction from a to b: the line of the crash.
    normal = offset / distance

    # How much of the push each car takes: half each, or all of it for the
    # car that can still move when the other is a wreck.
    share_a = 0 if a.wrecked else (1 if b.wrecked else 0.5)
    share_b = 1 - share_a

    # 1. Push them apart so they no longer overlap.
    overlap = touching - distance
    a.pos -= normal * overlap * share_a
    b.pos += normal * overlap * share_b
    a.sync_rect()
    b.sync_rect()

    # 2. Closing speed: how fast they move towards each other along the
    # crash line. If it's 0 or less they're already moving apart: no bounce.
    closing = (a.velocity - b.velocity).dot(normal)
    if closing <= 0:
        return 0

    # 3. Bounce: take that closing speed away and send some of it back the
    # other way (CAR_BOUNCE, the same as for barriers), shared between the cars.
    change = closing * (1 + settings.CAR_BOUNCE)
    a.velocity -= normal * change * share_a
    b.velocity += normal * change * share_b
    return closing
