from enum import Enum
from typing import NamedTuple
import random
import sys

import glm
import glfw
from pygame import mixer


from resource_manager import ResourceManager
from sprite_renderer import SpriteRenderer
from game_object import GameObject
from ball_object import BallObject
from particle_generator import ParticleGenerator
from post_processor import PostProcessor
from text_renderer import TextRenderer
from game_level import GameLevel
from texture2d import Texture2D


# Represents the current state of the game
class GameState(Enum):
    GAME_ACTIVE = 0
    GAME_MENU = 1
    GAME_WIN = 2


# Represents the four possible (collision) directions
class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


# Defines a Collision typedef that represents collision data
# collision?, what direction?, difference vector center - closest point
class Collision(NamedTuple):
    is_collision: bool
    direction: Direction
    position: glm.vec2


# PowerUp inherits its state and rendering functions from
# GameObject but also holds extra information to state its
# active duration and whether it is activated or not.
# The type of PowerUp is stored as a string.
class PowerUp(GameObject):
    def __init__(self, type: str, color: glm.vec3, duration: float, position: glm.vec2, texture: Texture2D) -> None:
        super().__init__(position, glm.vec2(60.0, 20.0),
                         texture, color, glm.vec2(0.0, 150.0))
        self.type = type
        self.duration = duration
        self.activated = False


# calculates which direction a vector is facing (N,E,S or W)
def vectorDirection(target: glm.vec2) -> Direction:
    compass: list[glm.vec2] = [
        glm.vec2(0.0, 1.0),  # up
        glm.vec2(1.0, 0.0),  # right
        glm.vec2(0.0, -1.0),  # down
        glm.vec2(-1.0, 0.0)  # left
    ]
    max = 0.0
    best_match = -1
    for i in range(4):
        dot_product = glm.dot(glm.normalize(target), compass[i])
        if dot_product > max:
            max = dot_product
            best_match = i
    return Direction(best_match)


def isOtherPowerUpActive(powerups: list[PowerUp], type: str) -> bool:
    # Check if another PowerUp of the same type is still active
    # in which case we don't disable its effect (yet)
    for powerup in powerups:
        if powerup.activated:
            if powerup.type == type:
                return True
    return False


def shouldSpawn(chance: int) -> bool:
    rand_int = random.randint(0, sys.maxsize) % chance
    return rand_int == 0

# AABB - AABB collision


def checkCollision(one: GameObject, two: GameObject) -> bool:
    # collision x-axis?
    collision_x = (one.position.x + one.size.x >= two.position.x) and \
        (two.position.x + two.size.x >= one.position.x)
    # collision y-axis?
    collision_y = (one.position.y + one.size.y >= two.position.y) and \
        (two.position.y + two.size.y >= one.position.y)
    # collision only if on both axes
    return collision_x and collision_y


# AABB - Circle collision
def ballCheckCollision(one: BallObject, two: GameObject) -> Collision:
    # get center point circle first
    center = glm.vec2(one.position + one.radius)
    # cacluate AABB info (center, half-extents)
    aabb_half_extents = glm.vec2(two.size.x / 2.0, two.size.y / 2.0)
    aabb_center = glm.vec2(two.position.x + aabb_half_extents.x,
                           two.position.y + aabb_half_extents.y)
    # get difference vector between both centers
    difference = center - aabb_center
    clamped = glm.clamp(difference, -aabb_half_extents, aabb_half_extents)
    # now that we know the clamped values, add this to AABB_center and we get the value of box closest to circle
    closest = aabb_center + clamped
    # now retrieve vector between center circle and closest point AABB and check if length < radius
    difference = closest - center
    # not <= since in that case a collision also occurs when object one exactly
    # touches object two, which they are at the end of each collision resolution stage.
    if glm.length(difference) < one.radius:
        return Collision(True, vectorDirection(difference), difference)
    else:
        return Collision(False, Direction.UP, glm.vec2(0.0, 0.0))


# Game holds all game-related state and functionality.
# Combines all game-related data into a single class for
# easy access to each of the components and manageability.
class Game:
    def __init__(self, width: int, height: int) -> None:
        self.state = GameState.GAME_MENU
        self.keys: list[bool] = [False] * 1024
        self.keys_processed: list[bool] = [False] * 1024
        self.width = width
        self.height = height
        self.levels: list[GameLevel] = []
        self.powerups: list[PowerUp] = []
        self.level = 0
        self.lives = 3
        self.shake_time = 0.0
        # Initial velocity of the Ball
        self.initial_ball_velocity = (100.0, -350.0)
        # Radius of the ball object
        self.ball_radius = 12.5
        # Initial size of the player paddle
        self.player_size = glm.vec2(300.0, 20.0)
        # Initial velocity of the player paddle
        self.player_velocity = 500.0
        mixer.init()

    def init(self) -> None:
        # load shaders
        ResourceManager.loadShader("sprite.vs", "sprite.fs", None, "sprite")
        ResourceManager.loadShader(
            "particle.vs", "particle.fs", None, "particle")
        ResourceManager.loadShader(
            "post_processing.vs", "post_processing.fs", None, "postprocessing")
        # configure shaders
        projection = glm.ortho(0.0, float(self.width),
                               float(self.height), 0.0, -1.0, 1.0)
        ResourceManager.getShader("sprite").use()
        ResourceManager.getShader("sprite").setInteger("sprite", 0)
        ResourceManager.getShader("sprite").setMatrix4(
            "projection", projection)
        ResourceManager.getShader("particle").use()
        ResourceManager.getShader("particle").setInteger("sprite", 0)
        ResourceManager.getShader("particle").setMatrix4(
            "projection", projection)
        # load textures
        ResourceManager.loadTexture(
            "textures/background.jpg", False, "background")
        ResourceManager.loadTexture("textures/awesomeface.png", True, "face")
        ResourceManager.loadTexture("textures/block.png", False, "block")
        ResourceManager.loadTexture(
            "textures/block_solid.png", False, "block_solid")
        ResourceManager.loadTexture("textures/paddle.png", True, "paddle")
        ResourceManager.loadTexture("textures/particle.png", True, "particle")
        ResourceManager.loadTexture(
            "textures/powerup_speed.png", True, "powerup_speed")
        ResourceManager.loadTexture(
            "textures/powerup_sticky.png", True, "powerup_sticky")
        ResourceManager.loadTexture(
            "textures/powerup_increase.png", True, "powerup_increase")
        ResourceManager.loadTexture(
            "textures/powerup_confuse.png", True, "powerup_confuse")
        ResourceManager.loadTexture(
            "textures/powerup_chaos.png", True, "powerup_chaos")
        ResourceManager.loadTexture(
            "textures/powerup_passthrough.png", True, "powerup_passthrough")
        # set render-specific controls
        self.renderer = SpriteRenderer(ResourceManager.getShader("sprite"))
        self.particles = ParticleGenerator(ResourceManager.getShader("particle"),
                                           ResourceManager.getTexture("particle"), 500)
        self.effects = PostProcessor(ResourceManager.getShader(
            "postprocessing"), self.width, self.height)
        self.text = TextRenderer(self.width, self.height)
        self.text.load("fonts/OCRAEXT.TTF", 24)
        # load levels
        one = GameLevel()
        one.load("levels/one.lvl", self.width, self.height / 2)
        two = GameLevel()
        two.load("levels/two.lvl", self.width, self.height / 2)
        three = GameLevel()
        three.load("levels/three.lvl", self.width, self.height / 2)
        four = GameLevel()
        four.load("levels/four.lvl", self.width, self.height / 2)
        self.levels.append(one)
        self.levels.append(two)
        self.levels.append(three)
        self.levels.append(four)
        self.level = 0
        # configure game objects
        player_pos = glm.vec2(
            self.width / 2.0 - self.player_size.x / 2.0, self.height - self.player_size.y)
        self.player = GameObject(
            player_pos, self.player_size, ResourceManager.getTexture("paddle"))
        ball_pos = player_pos + \
            glm.vec2(self.player_size.x / 2 -
                     self.ball_radius, -self.ball_radius * 2.0)
        tempx, tempy = self.initial_ball_velocity
        self.ball = BallObject(ball_pos, self.ball_radius, glm.vec2(
            tempx, tempy), ResourceManager.getTexture("face"))

        # audio
        self.box_sound = mixer.Sound("audio/bleep.mp3")
        self.solid_sound = mixer.Sound("audio/solid.wav")
        self.powerup_sound = mixer.Sound("audio/powerup.wav")
        self.pad_sound = mixer.Sound("audio/bleep.wav")
        mixer.music.load("audio/breakout.mp3")
        mixer.music.play(-1)

    def update(self, dt: float) -> None:
        # update objects
        self.ball.move(dt, self.width)

        # check for collisions
        self.doCollisions()
        # update particles
        self.particles.update(
            dt, self.ball, 2, glm.vec2(self.ball.radius / 2.0))
        # update PowerUps
        self.updatePowerUps(dt)
        # reduce shake time
        if self.shake_time > 0.0:
            self.shake_time -= dt
            if self.shake_time <= 0.0:
                self.effects.shake = False
        # check loss condition
        if self.ball.position.y >= self.height:  # did ball reach bottom edge?
            self.lives = self.lives - 1
            # did the player lose all his lives? : game over
            if self.lives == 0:
                self.resetLevel()
                self.state = GameState.GAME_MENU
            self.resetPlayer()
        # check win condition
        if self.state == GameState.GAME_ACTIVE and self.levels[self.level].isCompleted():
            self.resetLevel()
            self.resetPlayer()
            self.effects.chaos = True
            self.state = GameState.GAME_WIN

    # game loop
    def processInput(self, dt: float) -> None:
        if self.state == GameState.GAME_MENU:
            if self.keys[glfw.KEY_ENTER] and (not self.keys_processed[glfw.KEY_ENTER]):
                self.state = GameState.GAME_ACTIVE
                self.keys_processed[glfw.KEY_ENTER] = True
            if self.keys[glfw.KEY_W] and (not self.keys_processed[glfw.KEY_W]):
                if self.level < 3:
                    self.level = self.level + 1
                else:
                    self.level = 0
                self.keys_processed[glfw.KEY_W] = True
            if self.keys[glfw.KEY_S] and (not self.keys_processed[glfw.KEY_S]):
                if self.level > 0:
                    self.level = self.level - 1
                else:
                    self.level = 3
                self.keys_processed[glfw.KEY_S] = True
        if self.state == GameState.GAME_WIN:
            if self.keys[glfw.KEY_ENTER]:
                self.keys_processed[glfw.KEY_ENTER] = True
                self.effects.chaos = False
                self.state = GameState.GAME_MENU
        if self.state == GameState.GAME_ACTIVE:
            velocity = self.player_velocity * dt
            # move playerboard
            if self.keys[glfw.KEY_A]:
                if self.player.position.x >= 0.0:
                    self.player.position.x -= velocity
                    if self.ball.stuck:
                        self.ball.position.x -= velocity
            if self.keys[glfw.KEY_D]:
                if self.player.position.x <= self.width - self.player.size.x:
                    self.player.position.x += velocity
                    if self.ball.stuck:
                        self.ball.position.x += velocity
            if self.keys[glfw.KEY_SPACE]:
                self.ball.stuck = False

    def render(self) -> None:
        if self.state == GameState.GAME_ACTIVE or self.state == GameState.GAME_MENU or self.state == GameState.GAME_WIN:
            # begin rendering to postprocessing framebuffer
            self.effects.beginRender()
            # draw background
            background_texture = ResourceManager.getTexture("background")
            self.renderer.drawSprite(background_texture, glm.vec2(
                0.0, 0.0), glm.vec2(self.width, self.height), 0.0)
            # draw level
            self.levels[self.level].draw(self.renderer)
            # draw player
            self.player.draw(self.renderer)
            # draw PowerUps
            for powerup in self.powerups:
                if not powerup.destroyed:
                    powerup.draw(self.renderer)
            # draw particles
            self.particles.draw()
            # draw ball
            self.ball.draw(self.renderer)
            # end rendering to mpostprocessing framebuffer
            self.effects.endRender()
            # render postprocessing quad
            self.effects.render(glfw.get_time())
            # render text (don't include in postprocessing)
            ss = "".join(["Lives:", str(self.lives)])
            self.text.renderText(ss, 5.0, 5.0, 1.0)
            ss = "".join(["Current Level:", str(self.level)])
            self.text.renderText(ss, 5.0, 45.0, 1.0)
        if self.state == GameState.GAME_MENU:
            self.text.renderText("Press ENTER to start",
                                 250.0, self.height / 2.0, 1.0)
            self.text.renderText("Press W or S to select level",
                                 245.0, self.height / 2.0 + 20.0, 0.75)
        if self.state == GameState.GAME_WIN:
            self.text.renderText(
                "You WON!!!", 320.0, self.height / 2.0 - 20.0, 1.0, glm.vec3(0.0, 1.0, 0.0))
            self.text.renderText("Press ENTER to retry or ESC to quit",
                                 130.0, self.height / 2.0, 1.0, glm.vec3(1.0, 1.0, 0.0))

    def resetLevel(self) -> None:
        if self.level == 0:
            self.levels[0].load("levels/one.lvl", self.width, self.height / 2)
        if self.level == 1:
            self.levels[1].load("levels/two.lvl", self.width, self.height / 2)
        if self.level == 2:
            self.levels[2].load("levels/three.lvl",
                                self.width, self.height / 2)
        if self.level == 3:
            self.levels[3].load("levels/four.lvl", self.width, self.height / 2)
        self.lives = 3

    def resetPlayer(self) -> None:
        # reset player/ball stats
        self.player.size = self.player_size
        self.player.position = glm.vec2(
            self.width / 2.0 - self.player_size.x / 2.0, self.height - self.player_size.y)
        ball_pos = self.player.position + \
            glm.vec2(self.player_size.x / 2 -
                     self.ball_radius, -self.ball_radius * 2.0)
        tempx, tempy = self.initial_ball_velocity
        self.ball.reset(ball_pos, glm.vec2(tempx, tempy))
        # also disable all active powerups
        self.effects.chaos = False
        self.effects.confuse = False
        self.ball.pass_through = False
        self.ball.sticky = False
        self.player.color = glm.vec3(1.0)
        self.ball.color = glm.vec3(1.0)

    def updatePowerUps(self, dt: float) -> None:
        for powerup in self.powerups:
            powerup.position += powerup.velocity * dt
            if powerup.activated:
                powerup.duration -= dt
                if powerup.duration <= 0.0:
                    # remove powerup from list
                    powerup.activated = False
                    # deactivate effects
                    if powerup.type == "sticky":
                        if not isOtherPowerUpActive(self.powerups, "sticky"):
                            # only reset if no other PowerUp of type sticky is active
                            self.ball.sticky = False
                            self.player.color = glm.vec3(1.0)
                    elif powerup.type == "pass-through":
                        if not isOtherPowerUpActive(self.powerups, "pass-through"):
                            # only reset if no other PowerUp of type pass-through is active
                            self.ball.pass_through = False
                            self.player.color = glm.vec3(1.0)
                    elif powerup.type == "confuse":
                        if not isOtherPowerUpActive(self.powerups, "confuse"):
                            # only reset if no other PowerUp of type confuse is active
                            self.effects.confuse = False
                    elif powerup.type == "chaos":
                        if not isOtherPowerUpActive(self.powerups, "chaos"):
                            # only reset if no other PowerUp of type chaos is active
                            self.effects.chaos = False
        # Remove all PowerUps from vector that are destroyed AND !activated (thus either off the map or finished)
        # Note we use a lambda expression to remove each PowerUp which is destroyed and not activated

        for p in self.powerups:
            if p.destroyed and (not p.activated):
                self.powerups.remove(p)

    def spawnPowerUps(self, block: GameObject) -> None:
        if shouldSpawn(75):  # 1 in 75 chance
            self.powerups.append(PowerUp("speed", glm.vec3(0.5, 0.5, 1.0), 0.0,
                                         block.position, ResourceManager.getTexture("powerup_speed")))
        if shouldSpawn(75):  # 1 in 75 chance
            self.powerups.append(PowerUp("sticky", glm.vec3(1.0, 0.5, 1.0), 20.0,
                                         block.position, ResourceManager.getTexture("powerup_sticky")))
        if shouldSpawn(75):  # 1 in 75 chance
            self.powerups.append(PowerUp("pass-through", glm.vec3(0.5, 1.0, 0.5), 10.0,
                                         block.position, ResourceManager.getTexture("powerup_passthrough")))
        if shouldSpawn(75):  # 1 in 75 chance
            self.powerups.append(PowerUp("pad-size-increase", glm.vec3(1.0, 0.6, 0.4), 0.0,
                                         block.position, ResourceManager.getTexture("powerup_increase")))
        if shouldSpawn(15):  # Negative powerups should spawn more often
            self.powerups.append(PowerUp("confuse", glm.vec3(1.0, 0.3, 0.3), 15.0,
                                         block.position, ResourceManager.getTexture("powerup_confuse")))
        if shouldSpawn(15):
            self.powerups.append(PowerUp("chaos", glm.vec3(0.9, 0.25, 0.25), 15.0,
                                         block.position, ResourceManager.getTexture("powerup_chaos")))

    def ActivatePowerUp(self, powerup: PowerUp) -> None:
        if powerup.type == "speed":
            self.ball.velocity *= 1.2
        elif powerup.type == "sticky":
            self.ball.sticky = True
            self.player.color = glm.vec3(1.0, 0.5, 1.0)
        elif powerup.type == "pass-through":
            self.ball.pass_through = True
            self.player.color = glm.vec3(1.0, 0.5, 0.5)
        elif powerup.type == "pad-size-increase":
            self.player.size.x += 50
        elif powerup.type == "confuse":
            if not self.effects.chaos:
                self.effects.confuse = True  # only activate if chaos wasn't already active
        elif powerup.type == "chaos":
            if not self.effects.confuse:
                self.effects.chaos = True

    def doCollisions(self):
        for box in self.levels[self.level].bricks:
            if not box.destroyed:
                collision = ballCheckCollision(self.ball, box)
                if collision.is_collision:  # if collision is true
                    # destroy block if not solid
                    if not box.is_solid:
                        box.destroyed = True
                        self.spawnPowerUps(box)
                        self.box_sound.play()
                    else:
                        # if block is solid, enable shake effect
                        self.shake_time = 0.05
                        self.effects.shake = True
                        self.solid_sound.play()
                    # collision resolution
                    dir = collision.direction
                    diff_vector = collision.position
                    if not (self.ball.pass_through and not box.is_solid):
                        # don't do collision resolution on non-solid bricks if pass-through is activated
                        if dir == Direction.LEFT or dir == Direction.RIGHT:  # horizontal collision
                            self.ball.velocity.x = -self.ball.velocity.x  # reverse horizontal velocity
                            # relocate
                            penetration = self.ball.radius - abs(diff_vector.x)
                            if dir == Direction.LEFT:
                                self.ball.position.x += penetration  # move ball to right
                            else:
                                self.ball.position.x -= penetration  # move ball to left
                        else:  # vertical collision
                            self.ball.velocity.y = -self.ball.velocity.y  # reverse vertical velocity
                            # relocate
                            penetration = self.ball.radius - abs(diff_vector.y)
                            if dir == Direction.UP:
                                self.ball.position.y -= penetration  # move ball back up
                            else:
                                self.ball.position.y += penetration  # move ball back down

        # also check collisions on PowerUps and if so, activate them
        for powerup in self.powerups:
            if not powerup.destroyed:
                # first check if powerup passed bottom edge, if so: keep as inactive and destroy
                if powerup.position.y >= self.height:
                    powerup.destroyed = True
                if checkCollision(self.player, powerup):
                    # collided with player, now activate powerup
                    self.ActivatePowerUp(powerup)
                    powerup.destroyed = True
                    powerup.activated = True
                    self.powerup_sound.play()

        # and finally check collisions for player pad (unless stuck)
        result = ballCheckCollision(self.ball, self.player)

        if not self.ball.stuck and result.is_collision:
            # check where it hit the board, and change velocity based on where it hit the board
            center_board = self.player.position.x + self.player.size.x / 2.0
            distance = (self.ball.position.x + self.ball.radius) - center_board
            percentage = distance / (self.player.size.x / 2.0)
            # then mvoe accordingly
            strength = 2.0
            old_velocity = self.ball.velocity
            temp_x, temp_y = self.initial_ball_velocity
            self.ball.velocity.x = temp_x * percentage * strength
            # keep speed consistent over both axes (multiply by length of old velocity, so total strength is not changed)
            self.ball.velocity = glm.normalize(
                self.ball.velocity) * glm.length(old_velocity)
            # fix sticky paddle
            self.ball.velocity.y = -1.0 * abs(self.ball.velocity.y)
            # if Sticky powerup is activated, also stick ball to paddle once new velocity vectors were calculated
            self.ball.stuck = self.ball.sticky
            self.pad_sound.play()
