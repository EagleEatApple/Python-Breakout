import glm
import freetype

from OpenGL.GL import *

from resource_manager import ResourceManager


# Holds all state information relevant to a character as loaded using FreeType
class Character:
    def __init__(self, texture_id, size, bearing, advance) -> None:
        # ID handle of the glyph texture
        self.texture_id = texture_id
        # size of glyph
        self.size = size
        # offset from baseline to left/top of glyph
        self.bearing = bearing
        # horizontal offset to advance to next glyph
        self.advance = advance


#  A renderer class for rendering text displayed by a font loaded using the
# FreeType library. A single font is loaded, processed into a list of
# Character items for later rendering.
class TextRenderer:
    def __init__(self, width: int, height: int) -> None:
        # load and configure shader
        self.text_shader = ResourceManager.loadShader(
            "text_2d.vs", "text_2d.fs", None, "text")
        self.text_shader.use()
        self.text_shader.setMatrix4("projection",
                                    glm.ortho(0.0, width, height, 0.0))
        self.text_shader.setInteger("text", 0)
        # configure VAO/VBO for texture quads
        self.vao = GLuint()
        glCreateVertexArrays(1, self.vao)
        self.vbo = GLuint()
        glCreateBuffers(1, self.vbo)
        glNamedBufferStorage(self.vbo, sizeof(GLfloat) * 6 * 4, None,
                             GL_DYNAMIC_STORAGE_BIT)
        glVertexArrayVertexBuffer(self.vao, 0, self.vbo, 0,
                                  4 * sizeof(GLfloat))
        glVertexArrayAttribFormat(self.vao, 0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexArrayAttribBinding(self.vao, 0, 0)
        glEnableVertexArrayAttrib(self.vao, 0)

        # holds a list of pre-compiled Characters
        self.Characters:dict[str, Character] = {}

    # pre-compiles a list of characters from the given font
    def load(self, font: str, font_size: int) -> None:
        # first clear the previously loaded Characters
        self.Characters.clear()
        # load font as face
        face = freetype.Face(font)
        #  set size to load glyphs as
        face.set_pixel_sizes(0, font_size)
        # disable byte-alignment restriction
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        # then for the first 128 ASCII characters, pre-load/compile their
        # characters and store them
        for i in range(128):
            # load character glyph
            face.load_char(chr(i))
            # generate texture
            tex_id = GLuint()
            glCreateTextures(GL_TEXTURE_2D, 1, tex_id)
            width = face.glyph.bitmap.width
            height = face.glyph.bitmap.rows
            left = face.glyph.bitmap_left
            top = face.glyph.bitmap_top
            adv = face.glyph.advance.x
            if (width > 0) and (height > 0):
                ctype_data = (ctypes.c_int8 * len(face.glyph.bitmap.buffer))(*face.glyph.bitmap.buffer)
                glTextureStorage2D(tex_id, 1, GL_R8, width, height)
                glTextureSubImage2D(tex_id, 0, 0, 0, width, height, GL_RED,
                                    GL_UNSIGNED_BYTE, ctype_data)
                glTextureParameteri(tex_id, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTextureParameteri(tex_id, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTextureParameteri(
                    tex_id, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTextureParameteri(
                    tex_id, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                character = Character(tex_id, glm.ivec2(width, height),
                                      glm.ivec2(left, top), adv)
            else:
                character = Character(tex_id, glm.ivec2(width, height),
                                      glm.ivec2(left, top), adv)
            self.Characters[chr(i)] = character

    # renders a string of text using the precompiled list of characters
    def renderText(self, text: str, x: float, y: float, scale: float,
                   color=glm.vec3(1.0)) -> None:
        # activate corresponding render state
        self.text_shader.use()
        self.text_shader.setVec3("textColor", color)
        glBindVertexArray(self.vao)
        # iterate through all characters
        for c in text:
            ch = self.Characters[c]
            xpos = x + ch.bearing.x * scale
            ypos = y + (self.Characters['H'].bearing.y - ch.bearing.y) * scale
            w = ch.size.x * scale
            h = ch.size.y * scale
            # update VBO for each character
            vertices = [
                # pos                  # tex
                xpos,     ypos + h,    0.0, 1.0,
                xpos + w, ypos,        1.0, 0.0,
                xpos,    ypos,        0.0, 0.0,
                xpos,     ypos + h,    0.0, 1.0,
                xpos + w, ypos + h,    1.0, 1.0,
                xpos + w, ypos,        1.0, 0.0
            ]
            ctype_vertices = (GLfloat * len(vertices))(*vertices)
            # render glyph texture over quad
            glBindTextureUnit(0, ch.texture_id)
            # update content of VBO memory
            glNamedBufferSubData(self.vbo, 0, sizeof(GLfloat)*6*4, ctype_vertices)
            # render quad
            glDrawArrays(GL_TRIANGLES, 0, 6)
            # now advance cursors for next glyph
            # bitshift by 6 to get value in pixels (1/64th times 2^6 = 64)
            x += (ch.advance >> 6) * scale
