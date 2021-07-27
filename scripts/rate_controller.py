from time import sleep

from PySimpleGUI.PySimpleGUI import SimpleButton
import pytomlpp
import PySimpleGUI as sg

import viroro.physics as ph
import viroro.render as render

VIEWPORT_SIZE = (1200, 600)


class SimpleVisualiser():
    def __init__(self):
        self.window_created = False

    def create_window(self):
        sg.theme("Reddit")
        self.viewport = render.Viewport(size=VIEWPORT_SIZE)
        self.window = sg.Window("DEBUG DRAW", [[self.viewport.sg_graph]], finalize=True)
        self.viewport.create_draw_options()
        self.window_opened = True

    def show(self, field):
        if not self.window_created:
            self.create_window()
            self.window_created = True

        zoom = 200
        offset = field.car.body.position * -zoom + (self.viewport.size[0]/2, self.viewport.size[1]/2)
        angle = field.car.body.angle
        self.viewport.set_view(zoom, offset, angle)
        self.viewport.show(field)
        event, values = self.window.read(timeout=0)

        if event == sg.WIN_CLOSED:
            raise KeyboardInterrupt("Debug window closed.")

    def close(self):
        self.window.close()
        self.window_created = False


class Controller():
    def __init__(self):
        pass

    def make_move(self, car: ph.Car):
        car.get_sensor_values()
        power = 100
        angle = 10
        car.control(power, angle)

FIELD_CONFIG = pytomlpp.load(open("big_car.toml"))
SIMULATION_TICKS = 60*2

sv = SimpleVisualiser()
field = ph.Field(FIELD_CONFIG)
controller = Controller()

for _ in range(SIMULATION_TICKS):
    controller.make_move(field.car)
    field.step()
    sleep(1/60)

for _ in range(SIMULATION_TICKS):
    controller.make_move(field.car)
    field.step()
    sv.show(field)
    sleep(1/60)

sv.close()