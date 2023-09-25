import glm
from OpenGL.GL import *

from texture2d import Texture2D
from shader import Shader


class SpriteRenderer:
    def __init__(self, shader:Shader)->None:
        self.shader = shader
        self.initRenderData()

    # Renders a defined quad textured with given sprite
    def drawSprite(self, texture:Texture2D, position:glm.vec2, size:glm.vec2, rotate:float, color=glm.vec3(1.0))->None:
        # prepare transformations
        self.shader.use()
        model = glm.mat4(1.0)
        # first translate (transformations are: scale happens first, then rotation, and then final translation happens; reversed order)
        model = glm.translate(model, glm.vec3(position, 0.0))

        # move origin of rotation to center of quad
        model = glm.translate(model, glm.vec3(0.5 * size.x, 0.5 * size.y, 0.0))
        # then rotate
        model = glm.rotate(model, glm.radians(rotate), glm.vec3(0.0, 0.0, 1.0))
        # move origin back
        model = glm.translate(model, glm.vec3(-0.5 * size.x, -0.5 * size.y, 0.0))
        # last scale
        model = glm.scale(model, glm.vec3(size, 1.0))

        self.shader.setMatrix4("model", model)
        # render textured quad
        self.shader.setVec3("spriteColor", color)

        texture.bind(0)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

    # Initializes and configures the quad's buffer and vertex attributes
    def initRenderData(self)->None:
        # configure VAO/VBO
        # vertices = np.array([
        #     # pos     # tex
        #     0.0, 1.0, 0.0, 1.0,
        #     1.0, 0.0, 1.0, 0.0,
        #     0.0, 0.0, 0.0, 0.0, 
        #     0.0, 1.0, 0.0, 1.0,
        #     1.0, 1.0, 1.0, 1.0,
        #     1.0, 0.0, 1.0, 0.0
        # ], dtype=GLfloat)

        vertices = [
            # pos     # tex
            0.0, 1.0, 0.0, 1.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 
            0.0, 1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 1.0, 0.0
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

