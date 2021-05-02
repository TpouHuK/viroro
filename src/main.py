import window
import physics
from test_items import car_1, circle_1, walls_1, walls_2

def algo(car):
    sensors = car.get_sensor_values()
    p = sensors[2] - sensors[3]
    spd = 10
    car.steer(p*30)
    car.push(spd)

car = car_1(position=(0.5, 3.5), group=1)
car.algo = algo
walls = walls_2()

circle1 = circle_1(position=(1, 3))
circle2 = circle_1(position=(2, 2))
circle1.bump((6, 10))
circle2.bump((-6, -5))

items = [walls, circle1, circle2, car]

p_field = physics.PymunkField()
p_field.add(*items)

def debug():
    #car.sensors[0].make_reading()
    print(round(car.sensors[0].read_distance()*100, 2))

window.test_gui_1(p_field, car, items, debug)
