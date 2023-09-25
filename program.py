import sys
parent_dir = "../Python-Breakout"
sys.path.append(parent_dir)

import glfw
from glfw import _GLFWwindow as GLFWwindow
from OpenGL.GL import *


from resource_manager import ResourceManager
from game import Game

# The Width of the screen
SCREEN_WIDTH = 800
# The height of the screen
SCREEN_HEIGHT = 600

Breakout = Game(SCREEN_WIDTH, SCREEN_HEIGHT)
from pygame import mixer

def main():
    glfw.init()
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.RESIZABLE, False)
    window = glfw.create_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Python3/OpenGL 4.6 Breakout", None, None)
    if (window == None):
        print("Failed to create GLFW window")
        glfw.terminate()

    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_callback)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)

    # OpenGL configuration
    # --------------------
    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # initialize game
    Breakout.init()

    # deltaTime variables
    # -------------------
    delta_time = 0.0
    last_frame = 0.0

    while not glfw.window_should_close(window):
        # calculate delta time
        # --------------------
        current_frame = glfw.get_time()
        delta_time = current_frame - last_frame
        last_frame = current_frame
        glfw.poll_events()

        # manage user input
        # -----------------
        Breakout.processInput(delta_time)

        # update game state
        # -----------------
        Breakout.update(delta_time)
        
        # render
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        Breakout.render()

        glfw.swap_buffers(window)
    # delete all resources as loaded using the resource manager
    # ---------------------------------------------------------
    ResourceManager.clear()
    mixer.music.stop()
    mixer.quit()
    glfw.destroy_window(window)
    glfw.terminate()

def key_callback(window: GLFWwindow, key:int, scancode:int, action:int, mods:int)-> None:
    # when a user presses the escape key, we set the WindowShouldClose property to true, closing the application
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if key >= 0 and key < 1024:
        if action == glfw.PRESS:
            Breakout.keys[key] = True
        elif action == glfw.RELEASE:
            Breakout.keys[key] = False
            Breakout.keys_processed[key] = False

def framebuffer_size_callback(window: GLFWwindow, width: int, height: int) -> None:
    # make sure the viewport matches the new window dimensions; note that width and 
    # height will be significantly larger than specified on retina displays.
    glViewport(0, 0, width, height)

if __name__ == "__main__":
    main()