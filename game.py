"""
Game logic
"""

from constants import *

def allowed_position(m, position):
    """Returns True if pacman is allowed to be in the given position"""
    x, y = position
    object = m[x][y]

    return object in ALLOWED_OBJECTS
