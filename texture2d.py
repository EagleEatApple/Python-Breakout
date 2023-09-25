from OpenGL.GL import *


# Texture2D is able to store and configure a texture in OpenGL.
# It also hosts utility functions for easy management.
class Texture2D:
    def __init__(self) -> None:
        self.tex_id = GLuint()
        glCreateTextures(GL_TEXTURE_2D, 1, self.tex_id)
        self.width = 0
        self.height = 0
        self.internal_format = GL_RGB32F
        self.image_format = GL_RGB
        self.wrap_s = GL_REPEAT
        self.wrap_t = GL_REPEAT
        self.filter_min = GL_LINEAR
        self.filter_max = GL_LINEAR

    # generates texture from image data
    def generate(self, width: int, height: int, data: ctypes.c_void_p) -> None:
        self.width = width
        self.height = height
        # create Texture
        glTextureStorage2D(self.tex_id, 1, self.internal_format, width, height)
        glTextureSubImage2D(self.tex_id, 0, 0, 0, width, height, self.image_format, GL_UNSIGNED_BYTE, data)
        # set Texture wrap and filter modes
        glTextureParameteri(
            self.tex_id, GL_TEXTURE_MIN_FILTER, self.filter_min)
        glTextureParameteri(
            self.tex_id, GL_TEXTURE_MAG_FILTER, self.filter_max)
        glTextureParameteri(
            self.tex_id, GL_TEXTURE_WRAP_S, self.wrap_s)
        glTextureParameteri(
            self.tex_id, GL_TEXTURE_WRAP_T, self.wrap_t)

    # binds the texture as the current active GL_TEXTURE_2D texture object
    def bind(self, index: int) -> None:
        glBindTextureUnit(index, self.tex_id)
