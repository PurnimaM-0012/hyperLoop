# settings.py
# All the game's fixed numbers live here, so you can tweak them in one place.
# Level layouts (walls, parts, the machine) live in the levels/ folder.

import os

# --- Files and folders ---
# BASE_DIR is the folder this file is in, so paths work wherever you run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVELS_DIR = os.path.join(BASE_DIR, "levels")
TRACKS_DIR = os.path.join(LEVELS_DIR, "tracks")
TILES_FILE = os.path.join(LEVELS_DIR, "tiles.json")  # the tile legend
ASSETS_DIR = os.path.join(BASE_DIR, "assets")        # your tile images go in assets/tiles/
SAVE_PATH = os.path.join(BASE_DIR, "save.json")

# --- Window ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
TITLE = "Time Loop"

# --- Map ---
TILE_SIZE = 32    # each map character is a 32 x 32 pixel square
HUD_HEIGHT = 64   # the bar at the top for the timer and text; the map starts below it
# Maps can be any size: the camera scrolls around maps bigger than the window.
# A map exactly 30 x 18 tiles fills the window below the HUD with no scrolling.

# --- Game loop ---
FPS = 60  # how many times per second the loop runs
MAX_DT = 0.05  # longest frame we allow, in seconds (see main.py)

# --- Player ---
PLAYER_SIZE = 24     # width and height of the player square, in pixels
PLAYER_SPEED = 200   # pixels per second

# --- Progress (what survives a loop reset) ---
START_LOOP_DURATION = 80  # seconds in the first loop (1 min 20 s, from the design doc)
START_BAG_CAPACITY = 1    # bag slots at the start of a new game
BAG_SLOTS_PER_LEVEL = 1   # extra slots for each level cleared (subject to change)
# Fixed level order = file names in levels/ (prison -> levels/prison.json).
LEVEL_ORDER = ["prison", "research_facility"]
DEBUG_RACE_BONUS = 20     # seconds the debug key T adds now and to future loops ("pretend I won a race")

# --- Time loop ---
WARNING_TIME = 10         # the timer turns red at or below this many seconds
MESSAGE_TIME = 1.5        # how long a short message stays on screen

# --- Machine, parts and the bag ---
PART_SIZE = 16
BAG_SLOT_SIZE = 22   # the slot boxes in the HUD, in pixels

# --- Car (Step 9). Speeds in pixels per second; "rates" are per second. ---
# These numbers ARE the car's feel. Arcade = quick, grippy, easy to drift.
CAR_LENGTH = 36
CAR_WIDTH = 20
CAR_HITBOX = 22             # square used for barrier collisions (simpler than a rotated box)
CAR_MAX_SPEED = 520
CAR_ACCELERATION = 420
CAR_BRAKE = 900             # braking is much stronger than accelerating
CAR_REVERSE_MAX_SPEED = 160
CAR_REVERSE_ACCELERATION = 300
CAR_DRAG = 0.6              # how fast speed fades when you let go (rolling resistance)
CAR_TURN_RATE = 150         # degrees per second at full steering (was 200: felt too twitchy)
CAR_FULL_STEER_SPEED = 120  # below this speed, steering is weaker (a parked car can't spin)
CAR_STEER_RESPONSE = 6      # how fast steering builds up / eases off: 1 / 6 s = about 0.17 s to full
CAR_HIGH_SPEED_STEER = 0.6  # at top speed you get 60% of the turn rate (calmer on straights)
CAR_GRIP = 8.0              # how fast sideways sliding is cancelled (high = grippy)
CAR_HANDBRAKE_GRIP = 1.2    # much lower grip with the handbrake on = drift
CAR_HANDBRAKE_DRAG = 1.5    # the handbrake also scrubs off some forward speed
CAR_HANDBRAKE_STEER = 1.3   # and lets you turn a little harder, to kick the back out
CAR_BOUNCE = 0.4            # fraction of speed kept (reversed) when hitting a barrier
OFFROAD_DRAG = 1.5          # extra drag on slow tiles like grass
SKID_SPEED = 90             # sideways speed above which tyres leave skid marks and dust
SPEED_DISPLAY_SCALE = 0.25  # pixels/second -> the "km/h" shown on the speedometer

# --- Race camera and effects ---
CAMERA_LOOKAHEAD = 0.3      # the camera aims where the car will be in 0.3 s
CAMERA_SMOOTHING = 6.0      # how quickly the camera catches up (higher = snappier)
SHAKE_MIN_IMPACT = 120      # hits slower than this don't shake the screen
SHAKE_PER_SPEED = 1 / 40    # shake (pixels) per unit of impact speed
SHAKE_MAX = 10              # strongest shake, in pixels
SHAKE_DECAY = 30            # pixels of shake lost per second

# --- Colours (red, green, blue), each from 0 to 255 ---
# Tile colours (walls, floor...) are in levels/tiles.json instead.
BACKGROUND = (24, 22, 20)   # dark, dusty brown-black for a ruined town
HUD_BAR = (16, 15, 14)      # the bar behind the timer
TEXT = (220, 210, 190)      # pale, faded white
DIM_TEXT = (130, 122, 110)  # hints and unselected menu items
HIGHLIGHT = (214, 120, 52)  # the selected menu item
PLAYER = (214, 120, 52)     # rusty orange, easy to spot
TIMER_WARNING = (225, 60, 50)  # red for the last seconds of a loop
MACHINE = (160, 150, 135)      # outline of the machine
EMPTY_SLOT = (55, 50, 46)      # a machine slot with no part in it
WIN = (120, 210, 110)          # green "cleared" text and built sub-parts
PORTAL_GLOW = (190, 140, 255)  # the pulsing ring around a portal
CAR_BODY = (214, 120, 52)      # same rusty orange as the player
CAR_FRONT = (120, 60, 25)      # darker front, so you can see which way it points
SKID_MARK = (22, 20, 18)       # tyre marks burnt into the road
ROAD_ARROW = (175, 160, 120)   # direction arrows painted on the track
DUST = (150, 135, 110)         # dust puffs when sliding
