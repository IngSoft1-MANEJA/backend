import enum

class Shapes(enum.Enum): # To define the shapes 
    circle = 'circle'
    square = 'square'
    triangle = 'triangle'
    star = 'star'
    
class Movements(enum.Enum): # To define the movements
    up = 'up'
    down = 'down'
    left = 'left'
    right = 'right'
    
class Colors(enum.Enum):
    red = 'red'
    green = 'green'
    blue = 'blue'
    yellow = 'yellow'