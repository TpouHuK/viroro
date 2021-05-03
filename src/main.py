import window
import physics
from math import sqrt
from test_items import car_1, walls_2


def algo(car):
    sensors = car.get_sensor_values()
    p = sensors[2] - sensors[3]
    spd = 20
    car.steer(p*100)
    car.push(spd)


car = car_1(position=(0.5, 3.5), group=1)
car.algo = algo
checkpoints = physics.CheckPoints(
        [
            (0.5, 2.5),
            (1.5, 0.5),
            (2.5, 1.5),
            (3.5, 2.5),
            (4.5, 1.5),
            (5.5, 0.5),
            (6.5, 1.5),
            (7.5, 2.5),
            (8.5, 3.0),
            (7.5, 3.5),
            (1.5, 3.5),
            ],
        detection_radius=0.5)
checkpoints.add_car(car)
walls = walls_2()

items = [walls, car, checkpoints]

p_field = physics.PymunkField()
p_field.add(*items)


def debug():
    #car.sensors[0].make_reading()
    print(round(car.sensors[0].read_distance()*100, 2))


window.test_gui_1(p_field, car, checkpoints, items, debug)
