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
# The tile 'P' (portal) links the two areas of a two-area level.
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
        }
    return tile_types


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
        self.part_tiles = []     # (symbol, tile rect) for each part digit

        # The map never changes while playing, so we draw it ONCE onto this
        # surface and just copy that picture every frame.
        self.background = pygame.Surface((self.width, self.height))

        for row, line in enumerate(rows):
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

                if tile_symbol not in tile_types:
                    raise ValueError(f"{where}: unknown symbol '{symbol}'. "
                                     f"Add it to levels/tiles.json")
                tile = tile_types[tile_symbol]
                if tile["image"] is not None:
                    self.background.blit(tile["image"], tile_rect)
                else:
                    pygame.draw.rect(self.background, tile["colour"], tile_rect)
                if tile["solid"]:
                    self.walls.append(tile_rect)


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
