from pymunk.vec2d import Vec2d
def m_to_pd(x):
    """Pymunk coordinates to screen coordinates."""
    OFFSET = Vec2d(int(m_to_p(0.1)), int(m_to_p(0.1)))
    return m_to_p(x)+OFFSET

def pd_to_m(x):
    raise NotImplemented

def m_to_p(x):
    """Translate pymunk values to pixels."""
    return x*TILE_SIZE

def p_to_m(x):
    """Translate pixels to pymunk values."""
    return x/TILE_SIZE

# Gui config
WINDOW_TITLE = "🔥 hot garbage"

TILE_SIZE = 110 # How many pixels in one pymunk unit (meter)
FIELD_SIZE = Vec2d(8, 6) # Field size in squares
FIELD_SIZE_PIXELS = m_to_p(Vec2d(FIELD_SIZE.x, FIELD_SIZE.y))

UPS = 60 # Pymunk updates per second
UPS_TICK = 1000/UPS
FPS = 60 # Screen redraws per second
FPS_TICK = 1000/FPS

# Pymunk config
WALL_THICKNESS = 0.01  # Segment wall added thickness
WALL_ELASTICITY = 0.999

ITERATIONS = 15 # Pymunk solver iterations
MICROSTEP_AMOUNT = 150 # Making lots of smaller steps for accuracy
STEP_SIZE = 1/UPS
MICROSTEP_SIZE = STEP_SIZE/MICROSTEP_AMOUNT
