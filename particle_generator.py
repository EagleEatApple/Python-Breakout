import random

import glm
from OpenGL.GL import *

from game_object import GameObject
from shader import Shader
from texture2d import Texture2D


# Represents a single particle and its state
class Particle:
    def __init__(self):
        self.position = glm.vec2(0.0)
        self.velocity = glm.vec2(0.0)
        self.color = glm.vec4(1.0)
        self.life = 0.0


# ParticleGenerator acts as a container for rendering a large number of
# particles by repeatedly spawning and updating particles and killing
# them after a given amount of time.
class ParticleGenerator:
    def __init__(self, shader: Shader, texture: Texture2D,
                 amount: int) -> None:
        self.shader = shader
        self.texture = texture
        self.amount = amount
        self.last_used_particle = 0
        self.init()

    # initializes buffer and vertex attributes
    def init(self) -> None:
        # set up mesh and attribute properties
        particle_quad = [
            0.0, 1.0, 0.0, 1.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0,

            0.0, 1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 1.0, 0.0
        ]
        ctype_particle_quad = (GLfloat * len(particle_quad))(*particle_quad)
        self.vao = GLuint()
        glCreateVertexArrays(1, self.vao)
        vbo = GLuint()
        glCreateBuffers(1, vbo)
        # fill mesh buffer
        glNamedBufferStorage(vbo, ctypes.sizeof(ctype_particle_quad), ctype_particle_quad,
                             GL_DYNAMIC_STORAGE_BIT)
        # set mesh attributes
        glVertexArrayVertexBuffer(self.vao, 0, vbo, 0, 4 * sizeof(GLfloat))
        glVertexArrayAttribFormat(self.vao, 0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexArrayAttribBinding(self.vao, 0, 0)
        glEnableVertexArrayAttrib(self.vao, 0)

        # create amount default particle instances
        self.particles: list[Particle] = []
        for i in range(self.amount):
            self.particles.append(Particle())

    # update all particles
    def update(self, dt: float, object: GameObject, new_particles: int,
               offset=glm.vec2(0.0, 0.0)) -> None:
        # add new particles
        for i in range(new_particles):
            unused_particle = self.firstUnusedParticle()
            self.respawnParticle(
                self.particles[unused_particle], object, offset)
        # update all particles
        for i in range(self.amount):
            p = self.particles[i]
            p.life -= dt  # reduce life
            if p.life > 0.0:
                # particle is alive, thus update
                p.position -= p.velocity * dt
                p.color.w -= dt * 2.5

    # render all particles
    def draw(self) -> None:
        # use use additive blending to give it a 'glow' effect
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        self.shader.use()
        for p in self.particles:
            if p.life > 0.0:
                self.shader.setVec2("offset", p.position)
                self.shader.setVec4("color", p.color)
                self.texture.bind(0)
                glBindVertexArray(self.vao)
                glDrawArrays(GL_TRIANGLES, 0, 6)
        # don't forget to reset to default blending mode
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # stores the index of the last particle used (for quick access to next
    # dead particle)
    def firstUnusedParticle(self) -> int:
        # first search from last used particle, this will usually return
        # almost instantly
        for i in range(self.last_used_particle, self.amount):
            if self.particles[i].life <= 0.0:
                self.last_used_particle = i
                return i
        # otherwise, do a linear search
        for i in range(self.last_used_particle):
            if self.particles[i].life <= 0.0:
                self.last_used_particle = i
                return i
        # all particles are taken, override the first one (note that if it
        # repeatedly hits this case, more particles should be reserved)
        self.last_used_particle = 0
        return 0

    # respawns particle
    def respawnParticle(self, particle: Particle, object: GameObject,
                        offset=glm.vec2(0.0, 0.0)) -> None:
        ran = random.uniform(-5.0, 4.9)
        rcolor = random.uniform(0.5, 1.49)
        particle.position = object.position + ran + offset
        particle.color = glm.vec4(rcolor, rcolor, rcolor, 1.0)
        particle.life = 1.0
        particle.velocity = object.velocity * 0.1
