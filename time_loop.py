# time_loop.py
# The countdown that drives the whole game. When it reaches zero, the
# current loop is over and everything that belongs to "this loop" resets.

import math


def format_time(seconds):
    """Seconds as minutes:seconds, e.g. 80 -> '1:20', 9.2 -> '0:10'.

    We round UP (math.ceil), like most countdowns: with 79.6 s left it
    still shows 1:20, and it shows 0:01 until the very last moment.
    """
    seconds = max(0, math.ceil(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"  # :02d pads 5 -> "05"


class TimeLoop:
    def __init__(self, duration):
        # How long a full loop lasts. main.py copies this from Progress at
        # every reset, so race wins make the NEXT loop longer.
        self.duration = duration
        # How many seconds are left in the current loop.
        self.time_left = duration

    def update(self, dt):
        """Count down by dt seconds. Returns True on the frame time runs out."""
        self.time_left -= dt
        return self.time_left <= 0

    def reset(self):
        """Refill the timer for a new loop."""
        self.time_left = self.duration

    def display_text(self):
        """The time left as minutes:seconds (see format_time above)."""
        return format_time(self.time_left)
