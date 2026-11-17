# settings.py
# All the game's fixed numbers live here, so you can tweak them in one place.

# --- Window ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
TITLE = "Time Loop"

# --- Game loop ---
FPS = 60  # how many times per second the loop runs
MAX_DT = 0.05  # longest frame we allow, in seconds (see main.py)

# --- Player ---
PLAYER_SIZE = 24     # width and height of the player square, in pixels
PLAYER_SPEED = 200   # pixels per second
PLAYER_START = (480, 320)  # where every loop begins (later: next to the machine)

# --- Progress (what survives a loop reset) ---
START_LOOP_DURATION = 80  # seconds in the first loop (1 min 20 s, from the design doc)
START_BAG_CAPACITY = 1    # bag slots at the start (used from Step 8)
LEVEL_ORDER = ["prison"]  # fixed level order; more locations are added later
LEVEL_NAMES = {"prison": "Prison"}
SAVE_FILE = "save.json"   # stored next to main.py
DEBUG_RACE_BONUS = 20     # seconds the debug key T adds ("pretend I won a race")

# --- Time loop ---
WARNING_TIME = 10         # the timer turns red at or below this many seconds
RESET_MESSAGE_TIME = 1.5  # how long "The loop resets..." stays on screen

# --- Machine and parts ---
# The machine stands just above the start point, so every loop begins there.
MACHINE_RECT = (444, 240, 96, 48)   # x, y, width, height
PART_SIZE = 16
# Each part: (name, (x, y) on the ground, colour). Positions are FIXED on
# purpose: knowledge persists between loops, so players can learn them.
PARTS = [
    ("Power cell",    (60, 60),   (235, 200, 70)),   # top-left corner, yellow
    ("Flux coil",     (890, 60),  (80, 200, 220)),   # top-right corner, cyan
    ("Control board", (747, 470), (120, 210, 110)),  # narrow alley, bottom-right, green
]

# --- Town ---
WALL_THICKNESS = 16  # the town's outer boundary

# --- Colours (red, green, blue), each from 0 to 255 ---
BACKGROUND = (24, 22, 20)   # dark, dusty brown-black for a ruined town
TEXT = (220, 210, 190)      # pale, faded white
WALL = (88, 82, 76)         # grey concrete of ruined buildings
PLAYER = (214, 120, 52)     # rusty orange, easy to spot
TIMER_WARNING = (225, 60, 50)  # red for the last seconds of a loop
MACHINE = (160, 150, 135)      # outline of the machine
EMPTY_SLOT = (55, 50, 46)      # a machine slot with no part in it
WIN = (120, 210, 110)          # green "You escaped!" text
