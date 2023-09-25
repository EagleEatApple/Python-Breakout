import glm

from texture2d import Texture2D
from game_object import GameObject


# BallObject holds the state of the Ball object inheriting
# relevant state data from GameObject. Contains some extra
# functionality specific to Breakout's ball object that
# were too specific for within GameObject alone.
class BallObject(GameObject):
    def __init__(self, pos: glm.vec2, radius: float, velocity: glm.vec2,
                 sprite: Texture2D) -> None:
        super().__init__(pos, glm.vec2(radius * 2.0, radius * 2.0),
                         sprite, glm.vec3(1.0), velocity)
        # ball state
        self.radius = radius
        self.stuck = True
        self.sticky = False
        self.pass_through = False

    # moves the ball, keeping it constrained within the window
    # bounds (except bottom edge); returns new position
    def move(self, dt: float, window_width: int) -> glm.vec2:
        # if not stuck to player board
        if not self.stuck:
            # move the ball
            self.position += self.velocity * dt
            # then check if outside window bounds and if so, reverse velocity
            # and restore at correct position
            if self.position.x <= 0.0:
                self.velocity.x = -self.velocity.x
                self.position.x = 0.0
            elif (self.position.x + self.size.x) >= window_width:
                self.velocity.x = -self.velocity.x
                self.position.x = window_width - self.size.x
            if self.position.y <= 0.0:
                self.velocity.y = -self.velocity.y
                self.position.y = 0.0
            return self.position

    # resets the ball to initial Stuck Position (if ball is outside
    # window bounds)
    def reset(self, position: glm.vec2, velocity: glm.vec2) -> None:
        self.position = position
        self.velocity = velocity
        self.stuck = True
        self.sticky = False
        self.pass_through = False
