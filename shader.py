from OpenGL.GL import *
import glm


#  General purpose shader object. Compiles from file, generates
# compile/link-time error messages and hosts several utility
# functions for easy management.
class Shader:
    def use(self) -> "Shader":
        glUseProgram(self.id)
        return self

    # compiles the shader from given source code
    def compile(self, vertex_source: str, fragment_source: str,
                geometry_source: str) -> None:
        # vertex Shader
        s_vertex = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(s_vertex, vertex_source)
        glCompileShader(s_vertex)
        self.checkCompileErrors(s_vertex, "VERTEX")
        # fragment Shader
        s_fragment = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(s_fragment, fragment_source)
        glCompileShader(s_fragment)
        self.checkCompileErrors(s_fragment, "FRAGMENT")
        # if geometry shader source code is given, also compile geometry shader
        if geometry_source is not None:
            g_shader = glCreateShader(GL_GEOMETRY_SHADER)
            glShaderSource(g_shader, geometry_source)
            glCompileShader(g_shader)
            self.checkCompileErrors(g_shader, "GEOMETRY")
        # shader program
        self.id = glCreateProgram()
        glAttachShader(self.id, s_vertex)
        glAttachShader(self.id, s_fragment)
        if geometry_source is not None:
            glAttachShader(self.id, g_shader)
        glLinkProgram(self.id)
        self.checkCompileErrors(self.id, "PROGRAM")
        # delete the shaders as they're linked into our program now and no
        # longer necessary
        glDeleteShader(s_vertex)
        glDeleteShader(s_fragment)
        if geometry_source is not None:
            glDeleteShader(g_shader)

    def setFloat(self, name: str, value: float, use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform1f(glGetUniformLocation(self.id, name), value)

    def setInteger(self, name: str, value: int, use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform1i(glGetUniformLocation(self.id, name), value)

    def setVector2f(self, name: str, x: float, y: float,
                    use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform2f(glGetUniformLocation(self.id, name), x, y)

    def setVec2(self, name: str, value: glm.vec2, use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform2f(glGetUniformLocation(self.id, name), value.x, value.y)

    def setVector3f(self, name: str, x: float, y: float, z: float,
                    use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform3f(glGetUniformLocation(self.id, name), x, y, z)

    def setVec3(self, name: str, value: glm.vec3, use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform3f(glGetUniformLocation(self.id, name),
                    value.x, value.y, value.z)

    def setVector4f(self, name: str, x: float, y: float, z: float, w: float,
                    use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform4f(glGetUniformLocation(self.id, name), x, y, z, w)

    def setVec4(self, name: str, value: glm.vec4, use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniform4f(glGetUniformLocation(self.id, name),
                    value.x, value.y, value.z, value.w)

    def setMatrix4(self, name: str, matrix: glm.mat4,
                   use_shader=False) -> None:
        if use_shader:
            self.use()
        glUniformMatrix4fv(glGetUniformLocation(
            self.id, name), 1, False, glm.value_ptr(matrix))

    def checkCompileErrors(self, object: int, type: str) -> None:
        if type != "PROGRAM":
            success = glGetShaderiv(object, GL_COMPILE_STATUS)
            if not success:
                info_log = glGetShaderInfoLog(object)
                print("| ERROR::SHADER: Compile-time error: Type: ", type)
                print(info_log)
                print("-- ------------------------------------------- --")
        else:
            success = glGetProgramiv(object, GL_LINK_STATUS)
            if not success:
                info_log = glGetProgramInfoLog(object)
                print("| ERROR::Shader: Link-time error: Type: ", type)
                print(info_log)
                print("-- ------------------------------------------- --")
