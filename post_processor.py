from OpenGL.GL import *

from texture2d import Texture2D
from shader import Shader


# PostProcessor hosts all PostProcessing effects for the Breakout
# Game. It renders the game on a textured quad after which one can
# enable specific effects by enabling either the Confuse, Chaos or
# Shake boolean.
# It is required to call BeginRender() before rendering the game
# and EndRender() after rendering the game for the class to work.
class PostProcessor:
    def __init__(self, shader: Shader, width: int, height: int) -> None:
        self.post_processing_shader = shader
        self.texture = Texture2D()
        self.width = width
        self.height = height
        self.confuse = False
        self.chaos = False
        self.shake = False
        # initialize renderbuffer/framebuffer object
        # MSFBO = Multisampled FBO. FBO is regular, used for blitting MS
        # color-buffer to texture
        self.msfbo = GLuint()
        glCreateFramebuffers(1, self.msfbo)
        self.fbo = GLuint()
        glCreateFramebuffers(1, self.fbo)
        # RBO is used for multisampled color buffer
        self.rbo = GLuint()
        glCreateRenderbuffers(1, self.rbo)
        # initialize renderbuffer storage with a multisampled color buffer
        #  (don't need a depth/stencil buffer)
        glBindFramebuffer(GL_FRAMEBUFFER, self.msfbo)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glNamedRenderbufferStorageMultisample(
            self.rbo, 4, GL_RGB, width, height)
        glNamedFramebufferRenderbuffer(
            self.msfbo, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.rbo)
        if (glCheckNamedFramebufferStatus(self.msfbo, GL_FRAMEBUFFER)
                != GL_FRAMEBUFFER_COMPLETE):
            print("ERROR::POSTPROCESSOR: Failed to initialize MSFBO")
        # also initialize the FBO/texture to blit multisampled color-buffer to
        #  used for shader operations (for postprocessing effects)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        self.texture.generate(width, height, None)
        glNamedFramebufferTexture(
            self.fbo, GL_COLOR_ATTACHMENT0, self.texture.tex_id, 0)
        if (glCheckNamedFramebufferStatus(self.fbo, GL_FRAMEBUFFER)
                != GL_FRAMEBUFFER_COMPLETE):
            print("ERROR::POSTPROCESSOR: Failed to initialize FBO")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # initialize render data and uniforms
        self.initRenderData()
        self.post_processing_shader.use()
        self.post_processing_shader.setInteger("scene", 0)
        offset = 1.0 / 300.0
        offsets = [
            -offset,  offset,
            0.0,     offset,
            offset,  offset,
            -offset,  0.0,
            0.0,     0.0,
            offset,  0.0,
            -offset, -offset,
            0.0,    -offset,
            offset, -offset
        ]
        ctype_offsets = (GLfloat * len(offsets))(*offsets)
        glUniform2fv(glGetUniformLocation(
            self.post_processing_shader.id, "offsets"), 9, ctype_offsets)
        edge_kernel = [
            -1, -1, -1,
            -1,  8, -1,
            -1, -1, -1
        ]
        ctype_edge_kernel = (GLuint * len(edge_kernel))(*edge_kernel)
        glUniform1iv(glGetUniformLocation(
            self.post_processing_shader.id, "edge_kernel"), 9, ctype_edge_kernel)
        blur_kernel = [
            1.0 / 16.0, 2.0 / 16.0, 1.0 / 16.0,
            2.0 / 16.0, 4.0 / 16.0, 2.0 / 16.0,
            1.0 / 16.0, 2.0 / 16.0, 1.0 / 16.0
        ]
        ctype_blur_kernel = (GLfloat * len(blur_kernel))(*blur_kernel)
        glUniform1fv(glGetUniformLocation(
            self.post_processing_shader.id, "blur_kernel"), 9, ctype_blur_kernel)

    # prepares the postprocessor's framebuffer operations before rendering
    # the game
    def beginRender(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, self.msfbo)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    # should be called after rendering the game, so it stores all the rendered
    # data into a texture object
    def endRender(self) -> None:
        # now resolve multisampled color-buffer into intermediate FBO to store
        # to texture
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.msfbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.fbo)
        glBlitNamedFramebuffer(self.msfbo, self.fbo,
                               0, 0, self.width, self.height,
                               0, 0, self.width, self.height,
                               GL_COLOR_BUFFER_BIT, GL_NEAREST)
        # binds both READ and WRITE framebuffer to default framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # renders the PostProcessor texture quad (as a screen-encompassing
    # large sprite)
    def render(self, time: float) -> None:
        # set uniforms/options
        self.post_processing_shader.use()
        self.post_processing_shader.setFloat("time", time)
        self.post_processing_shader.setInteger("confuse", self.confuse)
        self.post_processing_shader.setInteger("chaos", self.chaos)
        self.post_processing_shader.setInteger("shake", self.shake)
        # render textured quad
        self.texture.bind(0)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)


    # initialize quad for rendering postprocessing texture
    def initRenderData(self) -> None:
        # configure VAO/VBO
        vertices = [
            # pos         tex
            -1.0, -1.0, 0.0, 0.0,
            1.0,  1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 1.0,

            -1.0, -1.0, 0.0, 0.0,
            1.0, -1.0, 1.0, 0.0,
            1.0,  1.0, 1.0, 1.0
        ]
        ctype_vertices = (GLfloat * len(vertices))(*vertices)
        self.vao = GLuint()
        glCreateVertexArrays(1, self.vao)
        vbo = GLuint()
        glCreateBuffers(1, vbo)
        glNamedBufferStorage(vbo, ctypes.sizeof(ctype_vertices), ctype_vertices,
                             GL_DYNAMIC_STORAGE_BIT)
        glVertexArrayVertexBuffer(self.vao, 0, vbo, 0, 4 * sizeof(GLfloat))
        glVertexArrayAttribFormat(self.vao, 0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexArrayAttribBinding(self.vao, 0, 0)
        glEnableVertexArrayAttrib(self.vao, 0)
