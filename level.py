# level.py
# Builds a playable level from a text-map file in the levels/ folder.
#
# Each character in the map is one TILE_SIZE x TILE_SIZE square. What each
# character means is looked up in levels/tiles.json (the tile legend),
# except for these reserved OBJECT symbols, which stand on a '.' floor tile:
#   S = where the player starts each loop    M = the machine (can span tiles)
#   1-9 = machine parts, described in the level file's "parts" section

import json
import os

import pygame

import settings
from machine import Machine, Part

FLOOR_UNDER_OBJECTS = "."


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


class Level:
    def __init__(self, level_id):
        self.id = level_id
        with open(level_path(level_id)) as file:
            data = json.load(file)
        self.name = data["name"]
        rows = data["map"]
        self.check_size(rows)

        tile_types = load_tile_types()
        size = settings.TILE_SIZE

        self.walls = []      # rects of every solid tile
        self.start = None    # where the player's top-left corner starts
        self.parts = []
        machine_tiles = []

        # The map never changes while playing, so we draw it ONCE onto this
        # surface and just copy that picture every frame. Drawing 540 tiles
        # one by one, 60 times a second, would be wasted work.
        self.background = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.background.fill(settings.BACKGROUND)

        for row, line in enumerate(rows):
            for column, symbol in enumerate(line):
                # Screen position of this tile. The map starts below the HUD bar.
                x = column * size
                y = settings.HUD_HEIGHT + row * size
                tile_rect = pygame.Rect(x, y, size, size)
                where = f"{level_id}.json, map row {row + 1}, column {column + 1}"

                tile_symbol = symbol
                if symbol == "S":
                    if self.start is not None:
                        raise ValueError(f"{where}: only one S (start) is allowed")
                    # Centre the smaller player square inside the tile.
                    offset = (size - settings.PLAYER_SIZE) // 2
                    self.start = (x + offset, y + offset)
                    tile_symbol = FLOOR_UNDER_OBJECTS
                elif symbol == "M":
                    machine_tiles.append(tile_rect)
                    tile_symbol = FLOOR_UNDER_OBJECTS
                elif symbol.isdigit():
                    if symbol not in data["parts"]:
                        raise ValueError(f"{where}: part '{symbol}' isn't listed in \"parts\"")
                    info = data["parts"][symbol]
                    offset = (size - settings.PART_SIZE) // 2
                    part = Part(info["name"], (x + offset, y + offset), tuple(info["colour"]))
                    part.symbol = symbol
                    self.parts.append(part)
                    tile_symbol = FLOOR_UNDER_OBJECTS

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

        if self.start is None:
            raise ValueError(f"{level_id}.json: the map needs an S (start)")
        if not machine_tiles:
            raise ValueError(f"{level_id}.json: the map needs at least one M (machine)")
        if not self.parts:
            raise ValueError(f"{level_id}.json: the map needs at least one part (1-9)")

        # Keep parts in number order (1, 2, 3...), whatever order they appear in.
        self.parts.sort(key=lambda part: part.symbol)
        # One machine rect covering all its M tiles. unionall() returns the
        # smallest rect that contains every rect in the list.
        machine_rect = machine_tiles[0].unionall(machine_tiles[1:])
        self.machine = Machine(machine_rect, len(self.parts))

    def check_size(self, rows):
        """Give a clear error if the map isn't exactly the right size."""
        if len(rows) != settings.MAP_ROWS:
            raise ValueError(f"{self.id}.json: the map has {len(rows)} rows, "
                             f"it needs exactly {settings.MAP_ROWS}")
        for row, line in enumerate(rows):
            if len(line) != settings.MAP_COLUMNS:
                raise ValueError(f"{self.id}.json: map row {row + 1} is {len(line)} "
                                 f"characters, it needs exactly {settings.MAP_COLUMNS}")

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
