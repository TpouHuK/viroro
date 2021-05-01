import time
from collections import namedtuple
import PySimpleGUI as sg
import field
import physics as ph
import constants as cs

sg.theme("Reddit")

layout = [[sg.Button("Set angle", key="-SA-"), sg.Slider(range=(-45, 45), default_value=0, orientation="h", key="-ANGLE-")],
        [sg.Text("Thrust"), sg.Slider(range=(-100,100), default_value=0, orientation="h", key="-FORCE-")],
        [sg.Button("Do nothing"), sg.Button("Run", key="-PAUSE-", size=(5,1)), sg.Button("One step", key="-STEP-")],
        [sg.Text("TESTING IN PROGRESS", key="-TEXT-", size=(100, 2))],
            [sg.Graph(cs.FIELD_SIZE_PIXELS, 
                (0, 0), cs.FIELD_SIZE_PIXELS,
                key="-GRAPH-",
                enable_events=False,
                drag_submits=False)]]

window = sg.Window(cs.WINDOW_TITLE, layout, finalize=True)
canvas = window["-GRAPH-"].TKCanvas

p_field = ph.PymunkField()
car_props = {
    "wheel_radius": 0.035,
    "wheel_width": 0.025,
    "wheel_mass": 0.01,
    "wheel_slipforce": 60,
    "wheel_friction_force": 30,
    "wheel_side_friction": 0.5,
    "wheel_weird_forward_friction": 0.1,

    "tw": 0.10,
    "th": 0.20,
    "bw": 0.10,
    "bh": 0.20,
    
    "car_width": 0.25,
    "car_height": 0.30,
    "car_mass": 1.4,
    "hull_friction": 0.1,
    }

car = ph.Car(car_props, position=(0.5, 0.5))
circle = ph.Circle(position=(0.5, 3.5), mass=0.1,
        radius=0.15, elasticity=0.999)
walls = ph.Walls(field.walls, cs.WALL_THICKNESS, cs.WALL_ELASTICITY)

p_field.add(car, circle, walls)
to_show = [car, circle, walls]
circle.bump((0.3, 1))

def millis():
    return int(time.time()*1000)

free_time = 0
last_computation = 0
last_redraw = 0
fps = 0

comp_time = 0
draw_time = 0

running = False

while True:
    tick_start = millis()
    window["-TEXT-"].update(f"comp_time: {comp_time}, draw_time: {draw_time}")
    event, values = window.read(timeout=free_time)
    if event == sg.WIN_CLOSED:
        break

    if event == "-PAUSE-":
        running = not running
        window["-PAUSE-"].update("Pause" if running else "Run")

    if event == "-STEP-":
            p_field.step()

    if millis() - last_computation >= cs.UPS_TICK:
        last_computation = millis()
        if running:
            ang = values["-ANGLE-"]
            car.turn(-ang)
            car.push(-values["-FORCE-"]/1.5)
            p_field.step()

        comp_time = millis() - last_computation

    if millis() - last_redraw >= cs.FPS_TICK:
        last_redraw = millis()

        for item in to_show:
            item._show(canvas)

        draw_time = millis() - last_redraw

    free_time = int(max(0, cs.UPS_TICK - millis() + tick_start))/2

window.close()
