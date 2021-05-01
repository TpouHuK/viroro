from pymunk.vec2d import Vec2d
def m_to_pd(x):
    ''' Pymunk coordinates to screen coordinates [meters to pixels]
        for displaying on canvas'''
    OFFSET = Vec2d(int(m_to_p(0.1)), int(m_to_p(0.1)))
    return m_to_p(x)+OFFSET

def pd_to_m(x):
    raise NotImplemented

def m_to_p(x):
    ''' Pymunk values to screen values [meters to pixels] '''
    return x*TILE_SIZE

def p_to_m(x):
    ''' Screen values to pymunk values [pixels to meters] '''
    return x/TILE_SIZE

# Gui config
WINDOW_TITLE = "🔥 hot garbage"
#TILE_SIZE = 60
TILE_SIZE = 110

#FIELD_SIZE = Vec2d(15, 10) # Field size in squares
FIELD_SIZE = Vec2d(8, 6) # Field size in squares
FIELD_SIZE_PIXELS = m_to_p(Vec2d(FIELD_SIZE.x, FIELD_SIZE.y))

UPS = 60 # Pymunk updates per second
UPS_TICK = 1000/UPS
FPS = 60 # Redraws per second
FPS_TICK = 1000/FPS

# Pymunk config
WALL_THICKNESS = 0.01  # Segment wall added thickness
WALL_ELASTICITY = 0.999

ITERATIONS = 15 # Default 10
MICROSTEP_AMOUNT = 150
STEP_SIZE = 1/UPS
MICROSTEP_SIZE = STEP_SIZE/MICROSTEP_AMOUNT
