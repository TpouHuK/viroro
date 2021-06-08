import viroro.physics as ph
import pymunk
from pymunk import Vec2d


def test_distance_sensor():
    ph.DistanceSensor(
            pymunk.Body(),
            x=0, y=0, angle=0, range_=0, 
            beam_width=0, shape_filter=pymunk.ShapeFilter())
