import time
import window
import physics
from test_items import car_1, circle_1, walls_1

car = car_1(position=(0.5, 4))
walls = walls_1()

circle1 = circle_1(position=(1, 3))
circle2 = circle_1(position=(2, 2))
circle1.bump((6, 10))
circle2.bump((-6, -5))

items = [car, walls, circle1, circle2]

p_field = physics.PymunkField()
p_field.add(*items)

window.test_gui_1(p_field, car, items)
