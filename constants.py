HOST = 'localhost'
PORT = 2222
DIRECTIONS = ('up', 'right', 'down', 'left')

OBJECTS = {
    0: ('Empty', ' '),
    1: ('PacMan', '<'),
    2: ('PacDot', '*'),
    3: ('Fruit', 'O'),
    4: ('Wall', '|'),
    5: ('Blinky', 'B'),
    6: ('Pinky', 'P'),
    7: ('Inky', 'I'),
    8: ('Clyde', 'C')
}

PACMAN_TYPE = 1

GHOSTS = [5, 6, 7, 8]


ALLOWED_OBJECTS = [0, 1, 2, 3, 5, 6, 7, 8]
EATABLE_OBJECTS = [2, 3]
