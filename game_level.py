import glm

from game_object import GameObject
from resource_manager import ResourceManager
from sprite_renderer import SpriteRenderer


# GameLevel holds all Tiles as part of a Breakout level and
# hosts functionality to Load/render levels from the harddisk.
class GameLevel:
    def __init__(self) -> None:
        # level state
        self.bricks: list[GameObject] = []

    # loads level from file
    def load(self, file: str, level_width: int, level_height: int) -> None:
        # clear old data
        self.bricks.clear()
        tile_data: list[list[int]] = []
        # load from file
        with open(file) as file:
            # read each line from level file
            lines = file.readlines()
            for line in lines:
                # read each word separated by spaces
                data = line.split()
                row: list[int] = []
                for i in range(len(data)):
                    row.append(int(data[i]))
                tile_data.append(row)
            if len(tile_data) > 0:
                self.init(tile_data, level_width, level_height)

    # render level
    def draw(self, renderer: SpriteRenderer) -> None:
        for tile in self.bricks:
            if not tile.destroyed:
                tile.draw(renderer)

    # check if the level is completed (all non-solid tiles are destroyed)
    def isCompleted(self) -> bool:
        for tile in self.bricks:
            if (not tile.is_solid) and (not tile.destroyed):
                return False
        return True

    # initialize level from tile data
    def init(self, tile_data: list[list[int]], level_width: int,
             level_height: int) -> None:
        # calculate dimensions
        h = len(tile_data)
        w = len(tile_data[0])
        unit_width = level_width / float(w)
        unit_height = level_height / float(h)
        # initialize level tiles based on tileData
        for y in range(h):
            for x in range(w):
                # check block type from level data (2D level array)
                if tile_data[y][x] == 1:  # solid
                    pos = glm.vec2(unit_width * x, unit_height * y)
                    size = glm.vec2(unit_width, unit_height)
                    obj = GameObject(pos, size, ResourceManager.getTexture(
                        "block_solid"), glm.vec3(0.8, 0.8, 0.7))
                    obj.is_solid = True
                    self.bricks.append(obj)
                # non-solid, now determine its color based on level data
                elif tile_data[y][x] > 1:
                    color = glm.vec3(1.0)  # original: white
                    if tile_data[y][x] == 2:
                        color = glm.vec3(0.2, 0.6, 1.0)
                    elif tile_data[y][x] == 3:
                        color = glm.vec3(0.0, 0.7, 0.0)
                    elif tile_data[y][x] == 4:
                        color = glm.vec3(0.8, 0.8, 0.4)
                    elif tile_data[y][x] == 5:
                        color = glm.vec3(1.0, 0.5, 0.0)
                    pos = glm.vec2(unit_width * x, unit_height * y)
                    size = glm.vec2(unit_width, unit_height)
                    obj = GameObject(pos, size,
                                     ResourceManager.getTexture("block"),
                                     color)
                    self.bricks.append(obj)
