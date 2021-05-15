import viroro.physics as ph
import pymunk
from pymunk import Vec2d


def test_drawoptions():
    do = ph.DrawOptions(canvas=None, zoom=1)

    do.scale_screen(Vec2d.zero())
    do.to_screen(Vec2d.zero())


def test_distance_sensor():
    ph.DistanceSensor(
            pymunk.Body(),
            x=0, y=0, angle=0, range_=0, 
            beam_width=0, shape_filter=pymunk.ShapeFilter())


def test_drawoptions():
    v_one = Vec2d(1, 1)
    do = ph.DrawOptions(canvas=None, zoom=1)
    do.scale_screen(v_one)
