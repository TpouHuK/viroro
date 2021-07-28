import viroro.physics as physics
import viroro.render as render
import pytomlpp

def create_field(config_file):
    config = pytomlpp.load(open(config_file))
    car = physics.Car(config["car"])
    walls = physics.Walls(**config["walls"])
    checkpoints = physics.Checkpoints(**config["checkpoints"])

    dt = 1/config["pymunk_field"]["control_ups"]
    microsteps = int(dt*config["pymunk_field"]["simulation_ups"])
    pymunk_field = physics.PymunkField(dt, microsteps)
    pymunk_field.add(car, walls, checkpoints)

    return {
        "car": car,
        "walls": walls,
        "checkpoints": checkpoints,
        "pymunk_field": pymunk_field
        }


def draw_field(field, viewport):
    viewport.clear()
    viewport.render(field["car"], render.draw_car)
    viewport.render(field["walls"], render.draw_walls)
    viewport.render(field["checkpoints"], render.draw_checkpoints)


def set_camera_on_car(field, viewport, zoom=200):
    offset = field["car"].body.position * -zoom + (viewport.size[0]/2, viewport.size[1]/2)
    car_angle = field["car"].body.angle
    viewport.set_view(zoom, offset, car_angle)