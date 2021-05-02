import physics as ph

# i want dataclasses

def car_1(position, group):
    v_off = [0.14]*6
    h_off = [-0.06, -0.05, -0.03, 0.03, 0.05, 0.06]
    ang = [-90, 0, 45, -45, 0, 90]
    distance = [2]*6
    width = [0.001]*6
    sensors = []
    for i in range(6):
        sensors.append({
            "v_offset": v_off[i],
            "h_offset": h_off[i],
            "angle": ang[i],
            "distance": distance[i],
            "width": width[i],
            })

    car_props = {
        "wheel_radius": 0.035,
        "wheel_width": 0.020,
        "wheel_mass": 0.01,
        "wheel_slipforce": 60,
        "wheel_friction_force": 30,
        "wheel_side_friction": 0.5,
        "wheel_weird_forward_friction": 0.01,

        "tw": 0.10,
        "th": 0.20,
        "bw": 0.10,
        "bh": 0.20,
        
        "car_width": 0.25,
        "car_height": 0.30,
        "car_mass": 1.4,
        #"hull_friction": 0.1,
        "hull_friction": 0,
        "sensors": sensors,
    }
    return ph.Car(car_props, position, group)


def circle_1(position):
    return ph.Circle(
            position,
            mass=1.1, radius=0.15, elasticity=0.99)


def rect_walls(w, h, x=0, y=0):
    walls = [
            ((x+0, y+0), (x+0, y+h)),
            ((x+0, y+h), (x+w, y+h)),
            ((x+0, y+0), (x+w, y+0)),
            ((x+w, y+0), (x+w, y+h)),
            ] 
    return walls


def walls_1():
    return ph.Walls(rect_walls(7, 5), thickness=0.01, elasticity=0.999)

def walls_2():
    walls = [
            ((0, 0), (0, 4)),
            ((0, 4), (9, 4)),
            ((9, 4), (9, 2)),
            ((7, 2), (9, 2)),
            ((7, 0), (7, 2)),
            ((4, 0), (7, 0)),
            ((4, 0), (4, 2)),
            ((3, 2), (4, 2)),
            ((3, 0), (3, 2)),
            ((3, 0), (3, 2)),
            ((0, 0), (3, 0)),
            ((1, 1), (2, 1)),
            ((1, 1), (1, 3)),
            ((2, 1), (2, 3)),
            ((5, 1), (6, 1)),
            ((5, 1), (5, 3)),
            ((6, 1), (6, 3)),
            ((1, 3), (8, 3)),
            ]
    return ph.Walls(walls, thickness=0.01, elasticity=0.999)
