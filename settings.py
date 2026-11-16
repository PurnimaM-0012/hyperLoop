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

# --- Town ---
WALL_THICKNESS = 16  # the town's outer boundary

# --- Colours (red, green, blue), each from 0 to 255 ---
BACKGROUND = (24, 22, 20)   # dark, dusty brown-black for a ruined town
TEXT = (220, 210, 190)      # pale, faded white
WALL = (88, 82, 76)         # grey concrete of ruined buildings
PLAYER = (214, 120, 52)     # rusty orange, easy to spot
