import glm

from texture2d import Texture2D
from sprite_renderer import SpriteRenderer


# Container object for holding all state relevant for a single
# game object entity. Each object in the game likely needs the
# minimal of state as described within GameObject.
class GameObject:
    def __init__(self, pos: glm.vec2, size: glm.vec2,
                 sprite: Texture2D, color=glm.vec3(1.0),
                 velocity=glm.vec2(0.0)) -> None:
        self.position = pos
        self.size = size
        self.velocity = velocity
        self.color = color
        self.rotation = 0.0
        self.sprite = sprite
        self.is_solid = False
        self.destroyed = False

    # draw sprite
    def draw(self, renderer: SpriteRenderer) -> None:
        renderer.drawSprite(self.sprite, self.position, self.size,
                            self.rotation, self.color)
