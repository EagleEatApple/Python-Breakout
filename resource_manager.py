from OpenGL.GL import *
from PIL import Image

from texture2d import Texture2D
from shader import Shader


# A static singleton ResourceManager class that hosts several
# functions to load Textures and Shaders. Each loaded texture
# and/or shader is also stored for future reference by string
# handles. All functions and resources are static and no
# public constructor is defined.
class ResourceManager:
    # resource storage
    shaders:dict[str, Shader] = {}
    textures:dict[str, Texture2D] = {}

    # loads (and generates) a shader program from file loading vertex,
    # fragment (and geometry) shader's source code. If gShaderFile is
    # not nullptr, it also loads a geometry shader
    @staticmethod
    def loadShader(vShaderFile: str, fShaderFile: str, gShaderFile: str,
                   name: str) -> Shader:
        ResourceManager.shaders[name] = ResourceManager.loadShaderFromFile(
            vShaderFile, fShaderFile, gShaderFile)
        return ResourceManager.shaders[name]

    # retrieves a stored sader
    @staticmethod
    def getShader(name: str) -> Shader:
        return ResourceManager.shaders[name]

    # loads (and generates) a texture from file
    @staticmethod
    def loadTexture(file: str, alpha: bool, name: str) -> Texture2D:
        ResourceManager.textures[name] = ResourceManager.loadTextureFromFile(
            file, alpha)
        return ResourceManager.textures[name]

    # retrieves a stored texture
    @staticmethod
    def getTexture(name: str) -> Texture2D:
        return ResourceManager.textures[name]

    # properly de-allocates all loaded resources
    @staticmethod
    def clear() -> None:
        # (properly) delete all shaders
        for shader in ResourceManager.shaders.values():
            glDeleteProgram(shader.id)
        # (properly) delete all textures
        for tex in ResourceManager.textures.values():
            glDeleteTextures(1, tex.tex_id)

    # loads and generates a shader from file
    @staticmethod
    def loadShaderFromFile(vShaderFile: str, fShaderFile: str,
                           gShaderFile: str = None) -> Shader:
        # 1. retrieve the vertex/fragment source code from filePath
        try:
            # open files
            with open(vShaderFile) as file:
                vertex_code = file.read()
            with open(fShaderFile) as file:
                fragment_code = file.read()
            geometry_code = None
            # if geometry shader path is present, also load a geometry shader
            if gShaderFile is not None:
                with open(gShaderFile) as file:
                    geometry_code = file.read()
        except:
            print("ERROR::SHADER: Failed to read shader files")

        # 2. now create shader object from source code
        shader = Shader()
        shader.compile(vertex_code, fragment_code, geometry_code)
        return shader

    # loads a single texture from file
    @staticmethod
    def loadTextureFromFile(file: str, alpha: bool) -> Texture2D:
        # create texture object
        texture = Texture2D()
        if alpha:
            texture.internal_format = GL_RGBA32F
            texture.image_format = GL_RGBA
        # load image
        image = Image.open(file)
        width, height = image.size
        channels = len(image.getbands())
        # now generate texture
        texture.generate(width, height, image.tobytes())
        return texture
