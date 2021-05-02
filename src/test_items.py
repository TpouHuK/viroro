import physics as ph

def car_1(position):
    car_props = {
        "wheel_radius": 0.035,
        "wheel_width": 0.025,
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
        "hull_friction": 0.1,
    }
    return ph.Car(car_props, position)


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
