# level.py
# Builds a playable level from the files in the levels/ folder.
#
# A level is made of one or more AREAS. Each area is a text map: every
# character is one TILE_SIZE x TILE_SIZE square, and a map can be any size
# (the camera scrolls around big ones). What each character means is looked
# up in levels/tiles.json (the tile legend), except these reserved symbols,
# which stand on a '.' floor tile:
#   S = where every loop starts        M = the machine (can span tiles)
#   1-9 = machine parts, described in the level file's "parts" section
#         (on a race TRACK the digits are checkpoints instead, see load_track)
# The tile 'P' (portal) links the two areas of a two-area level.
# On a track, '=' tiles are the start/finish line.
#
# Two level-file layouts are allowed:
#   one area:   {"name": ..., "parts": {...}, "map": [rows...]}
#   several:    {"name": ..., "parts": {...}, "start_area": "machine_room",
#                "areas": {"machine_room": "areas/machine_room.json", ...}}
#   where each area file is {"map": [rows...]}.

import json
import os

import pygame

import settings
from machine import Machine, Part

FLOOR_UNDER_OBJECTS = "."
PORTAL = "P"
FINISH_LINE = "="


def level_path(level_id):
    return os.path.join(settings.LEVELS_DIR, level_id + ".json")


def read_level_name(level_id):
    """Just the level's display name, e.g. 'Prison' (used by the menu)."""
    with open(level_path(level_id)) as file:
        return json.load(file)["name"]


def load_tile_types():
    """Read the tile legend: symbol -> {solid, colour, image}."""
    with open(settings.TILES_FILE) as file:
        data = json.load(file)
    tile_types = {}
    for symbol, info in data.items():
        if len(symbol) != 1:
            continue  # skip notes like "_help"; real symbols are 1 character
        image = None
        if "image" in info:
            image_path = os.path.join(settings.ASSETS_DIR, info["image"])
            # convert_alpha() turns the image into the screen's pixel format,
            # which makes drawing it much faster. Then scale it to one tile.
            image = pygame.image.load(image_path).convert_alpha()
            image = pygame.transform.scale(image, (settings.TILE_SIZE, settings.TILE_SIZE))
        tile_types[symbol] = {
            "solid": info.get("solid", False),
            "colour": tuple(info["colour"]),
            "image": image,
            "speed": info.get("speed", 1.0),  # 1 = normal; grass is slower
            "pattern": info.get("pattern"),   # "checker" for start/finish lines
            "arrow": info.get("arrow"),       # an angle to paint an arrow, or None
        }
    return tile_types


def draw_tile_markings(surface, tile, tile_rect):
    """Paint extra markings on a tile: a checkerboard or a direction arrow."""
    if tile["pattern"] == "checker":
        square = settings.TILE_SIZE // 4  # a 4 x 4 checkerboard
        for row in range(4):
            for column in range(4):
                if (row + column) % 2 == 1:  # every other square is black
                    pygame.draw.rect(surface, (20, 20, 20),
                                     (tile_rect.x + column * square, tile_rect.y + row * square, square, square))
    if tile["arrow"] is not None:
        # A chevron pointing right, then rotated to the tile's angle around
        # the tile's centre. Vector2.rotate() turns a point by an angle.
        centre = pygame.Vector2(tile_rect.center)
        shape = [(-9, -13), (10, 0), (-9, 13), (-3, 0)]
        points = [centre + pygame.Vector2(p).rotate(tile["arrow"]) for p in shape]
        pygame.draw.polygon(surface, settings.ROAD_ARROW, points)


def load_track(track_id):
    """Load a race track from levels/tracks/<track_id>.json.

    A track is just a text map, built with the same Area class as level maps,
    so it uses the same tile legend. 'S' marks where the car starts, and
    "start_angle" says which way it faces (0 = right, 90 = down).
    '=' tiles are the finish line, and the digits 1, 2, 3... are invisible
    CHECKPOINTS that must be driven through in that order before crossing
    the line counts as a lap. Without them you could just reverse over the
    line. Each checkpoint is usually a row of the same digit across the road.
    Returns (name, area, start_angle, checkpoints), where checkpoints is a
    list (checkpoint 1 first) of lists of tile rects.
    """
    file_name = os.path.join("tracks", track_id + ".json")
    with open(os.path.join(settings.LEVELS_DIR, file_name)) as file:
        data = json.load(file)
    area = Area(track_id, data["map"], load_tile_types(), file_name)
    if area.start_tile is None:
        raise ValueError(f"{file_name}: the track needs an S (car start)")
    if not area.finish_tiles:
        raise ValueError(f"{file_name}: the track needs a finish line (= tiles)")

    # Group the digit tiles by digit: {"1": [rect, rect...], "2": [...]}.
    # Area stores digits in part_tiles because on a level they are parts.
    by_digit = {}
    for symbol, tile_rect in area.part_tiles:
        by_digit.setdefault(symbol, []).append(tile_rect)
    digits = sorted(by_digit)
    # They must be 1, 2, 3... with no gaps, or a lap could never finish.
    expected = [str(n) for n in range(1, len(digits) + 1)]
    if digits != expected:
        raise ValueError(f"{file_name}: checkpoints must be numbered 1, 2, 3... "
                         f"with no gaps (found {digits})")
    checkpoints = [by_digit[digit] for digit in digits]
    return data["name"], area, data.get("start_angle", 0), checkpoints


class Area:
    """One map of a level. Everything here is in WORLD coordinates."""

    def __init__(self, name, rows, tile_types, source):
        self.name = name
        if not rows or any(len(line) != len(rows[0]) for line in rows):
            raise ValueError(f"{source}: every map row must be the same length")

        size = settings.TILE_SIZE
        self.width = len(rows[0]) * size
        self.height = len(rows) * size

        self.walls = []          # rects of every solid tile
        self.portal = None       # the rect of this area's P tile, if any
        self.start_tile = None   # the S tile, if this area has it
        self.machine_tiles = []  # the M tiles, if this area has the machine
        self.part_tiles = []     # (symbol, tile rect) for each digit (parts, or a track's checkpoints)
        self.finish_tiles = []   # the '=' tiles (a race track's finish line)
        # The "speed" of every tile, row by row, so cars can ask how fast
        # they're allowed to go where they are (grass is slower than road).
        self.speed_grid = []

        # The map never changes while playing, so we draw it ONCE onto this
        # surface and just copy that picture every frame.
        self.background = pygame.Surface((self.width, self.height))

        for row, line in enumerate(rows):
            self.speed_grid.append([])
            for column, symbol in enumerate(line):
                tile_rect = pygame.Rect(column * size, row * size, size, size)
                where = f"{source}, map row {row + 1}, column {column + 1}"

                tile_symbol = symbol
                if symbol == "S":
                    if self.start_tile is not None:
                        raise ValueError(f"{where}: only one S (start) is allowed")
                    self.start_tile = tile_rect
                    tile_symbol = FLOOR_UNDER_OBJECTS
                elif symbol == "M":
                    self.machine_tiles.append(tile_rect)
                    tile_symbol = FLOOR_UNDER_OBJECTS
                elif symbol.isdigit():
                    self.part_tiles.append((symbol, tile_rect))
                    tile_symbol = FLOOR_UNDER_OBJECTS
                elif symbol == PORTAL:
                    if self.portal is not None:
                        raise ValueError(f"{where}: only one P (portal) per area")
                    self.portal = tile_rect
                elif symbol == FINISH_LINE:
                    self.finish_tiles.append(tile_rect)

                if tile_symbol not in tile_types:
                    raise ValueError(f"{where}: unknown symbol '{symbol}'. "
                                     f"Add it to levels/tiles.json")
                tile = tile_types[tile_symbol]
                if tile["image"] is not None:
                    self.background.blit(tile["image"], tile_rect)
                else:
                    pygame.draw.rect(self.background, tile["colour"], tile_rect)
                draw_tile_markings(self.background, tile, tile_rect)
                if tile["solid"]:
                    self.walls.append(tile_rect)
                self.speed_grid[row].append(tile["speed"])

    def speed_at(self, point):
        """The speed multiplier of the tile under a world point (1 = normal)."""
        column = int(point[0] // settings.TILE_SIZE)
        row = int(point[1] // settings.TILE_SIZE)
        if 0 <= row < len(self.speed_grid) and 0 <= column < len(self.speed_grid[0]):
            return self.speed_grid[row][column]
        return 1.0


def centred_in(tile_rect, item_size):
    """Top-left position that centres a smaller square inside a tile."""
    offset = (settings.TILE_SIZE - item_size) // 2
    return (tile_rect.x + offset, tile_rect.y + offset)


class Level:
    def __init__(self, level_id):
        self.id = level_id
        source = f"{level_id}.json"
        with open(level_path(level_id)) as file:
            data = json.load(file)
        self.name = data["name"]
        # The level's race track (levels/tracks/<track>.json), or None
        # ("track": null) for a level with no race, like the Prison. And its
        # loop cap: the longest a loop can ever get in this level, however
        # good your race bonuses (see Progress.loop_length).
        self.track = data["track"]
        self.loop_cap = data["loop_cap"]
        tile_types = load_tile_types()

        # --- Build the areas ---
        if "map" in data:                      # a one-area level
            self.areas = {"main": Area("main", data["map"], tile_types, source)}
            self.start_area = "main"
        else:                                  # a level made of several areas
            self.areas = {}
            for area_name, file_name in data["areas"].items():
                with open(os.path.join(settings.LEVELS_DIR, file_name)) as file:
                    rows = json.load(file)["map"]
                self.areas[area_name] = Area(area_name, rows, tile_types, file_name)
            self.start_area = data["start_area"]
            if self.start_area not in self.areas:
                raise ValueError(f"{source}: start_area '{self.start_area}' isn't in \"areas\"")

        # --- The start point: exactly one S, in the start area ---
        starts = [area for area in self.areas.values() if area.start_tile is not None]
        if len(starts) != 1 or starts[0].name != self.start_area:
            raise ValueError(f"{source}: there must be exactly one S, in the "
                             f"start area '{self.start_area}'")
        self.start = centred_in(starts[0].start_tile, settings.PLAYER_SIZE)

        # --- The machine: all its M tiles in one area ---
        machine_areas = [area for area in self.areas.values() if area.machine_tiles]
        if len(machine_areas) != 1:
            raise ValueError(f"{source}: the M tiles (machine) must all be in one area")
        self.machine_area = machine_areas[0].name
        tiles = machine_areas[0].machine_tiles
        # unionall() returns the smallest rect that contains every rect in the list.
        machine_rect = tiles[0].unionall(tiles[1:])

        # --- Parts: each listed part appears exactly once, in any area ---
        self.parts = []
        for area in self.areas.values():
            for symbol, tile_rect in area.part_tiles:
                if symbol not in data["parts"]:
                    raise ValueError(f"{source}: part '{symbol}' is on the map "
                                     f"but isn't listed in \"parts\"")
                info = data["parts"][symbol]
                part = Part(info["name"], centred_in(tile_rect, settings.PART_SIZE),
                            tuple(info["colour"]), area.name)
                part.symbol = symbol
                self.parts.append(part)
        symbols = sorted(part.symbol for part in self.parts)
        if symbols != sorted(data["parts"]):
            raise ValueError(f"{source}: each part in \"parts\" must appear exactly "
                             f"once on the maps (found {symbols})")
        self.parts.sort(key=lambda part: part.symbol)  # 1, 2, 3...
        self.machine = Machine(machine_rect, len(self.parts))

        # --- Portals: in a two-area level, each area's P leads to the other ---
        self.portal_links = {}
        if len(self.areas) == 2:
            first, second = self.areas.values()
            if first.portal is None or second.portal is None:
                raise ValueError(f"{source}: both areas need a P (portal) tile")
            self.portal_links = {first.name: second.name, second.name: first.name}
        elif len(self.areas) > 2:
            raise ValueError(f"{source}: levels with more than 2 areas aren't supported yet")

    def portal_arrival(self, area_name):
        """Where the player lands when arriving in an area through its portal."""
        return centred_in(self.areas[area_name].portal, settings.PLAYER_SIZE)
