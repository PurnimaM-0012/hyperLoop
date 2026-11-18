# settings.py
# All the game's fixed numbers live here, so you can tweak them in one place.
# Level layouts (walls, parts, the machine) live in the levels/ folder.

import os

# --- Files and folders ---
# BASE_DIR is the folder this file is in, so paths work wherever you run from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVELS_DIR = os.path.join(BASE_DIR, "levels")
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
START_BAG_CAPACITY = 1    # bag slots at the start (used from Step 8)
# Fixed level order = file names in levels/ (prison -> levels/prison.json).
LEVEL_ORDER = ["prison", "research_facility"]
DEBUG_RACE_BONUS = 20     # seconds the debug key T adds ("pretend I won a race")

# --- Time loop ---
WARNING_TIME = 10         # the timer turns red at or below this many seconds
MESSAGE_TIME = 1.5        # how long a short message stays on screen

# --- Machine and parts ---
PART_SIZE = 16

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
