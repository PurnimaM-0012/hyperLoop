# rival.py
# The AI that drives a rival car (Step 11).
#
# The rival uses exactly the same Car as you, with the same settings. The
# only difference is WHO presses the keys: here, code decides each frame
# whether to accelerate, brake and steer, and then calls car.update() just
# like the RaceScene does for your keys.
#
# How it finds its way: the track file lists WAYPOINTS, points along the
# racing line in order. The rival steers towards the next one, and when it
# gets close, it aims for the one after. This is called "seek" steering, and
# it's how most simple racing AI works.

import math
import random

import pygame

import settings


class RivalDriver:
    def __init__(self, car, waypoints):
        self.car = car
        # Waypoints come in tiles (column, row); turn them into world pixels
        # at each tile's centre.
        size = settings.TILE_SIZE
        self.waypoints = [pygame.Vector2(col * size + size / 2, row * size + size / 2)
                          for col, row in waypoints]
        self.target = 0            # index of the waypoint it's heading for
        self.near_player = False   # was it near your car last frame? (for the rubber band)

    def controls(self):
        """Decide this frame's 'keys'. Returns (throttle, brake, steer, handbrake)."""
        car = self.car
        target = self.waypoints[self.target]
        reach = settings.RIVAL_WAYPOINT_REACH * settings.TILE_SIZE
        if car.pos.distance_to(target) < reach:
            # Close enough: aim for the next waypoint. % wraps back to the first.
            self.target = (self.target + 1) % len(self.waypoints)
            target = self.waypoints[self.target]

        # Which way would it have to face to point at the target?
        # atan2 turns a direction (x, y) into an angle, in the same system
        # as car.angle (0 = right, 90 = down).
        to_target = target - car.pos
        wanted = math.degrees(math.atan2(to_target.y, to_target.x))
        # The difference, wrapped into -180..180, so it always turns the
        # short way round (+ means the target is to its right).
        error = (wanted - car.angle + 540) % 360 - 180

        steer = 0
        if error > settings.RIVAL_STEER_DEADZONE:
            steer = 1
        elif error < -settings.RIVAL_STEER_DEADZONE:
            steer = -1
        # A sharp corner at speed: lift off and brake instead of accelerating.
        sharp_corner = abs(error) > settings.RIVAL_BRAKE_ANGLE
        too_fast = car.velocity.length() > settings.RIVAL_BRAKE_SPEED
        brake = sharp_corner and too_fast
        throttle = not brake
        return throttle, brake, steer, False  # the AI never uses the handbrake

    def rubber_band(self, player_car):
        """Near your car, flip a coin ONCE: 15% faster or 15% slower, until
        it's far from you again. (random.random() gives a number from 0 to 1,
        so '< 0.5' is true half the time: a coin flip.)"""
        distance = self.car.pos.distance_to(player_car.pos)
        near = distance < settings.RUBBER_BAND_DISTANCE * settings.TILE_SIZE
        if near and not self.near_player:
            if random.random() < 0.5:
                self.car.speed_factor = 1 + settings.RUBBER_BAND_CHANGE
            else:
                self.car.speed_factor = 1 - settings.RUBBER_BAND_CHANGE
        elif not near:
            self.car.speed_factor = 1.0
        self.near_player = near
