import PySimpleGUI as sg
from collections import namedtuple
import time

import field
import physics
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

window = sg.Window("🔥 hot garbage", layout, return_keyboard_events=True, finalize=True)
canvas = window["-GRAPH-"].TKCanvas

fd = physics.PhysicalField()

for wall in fd.get_walls_to_draw():
    tl, br = wall
    canvas.create_line(*tl, *br, fill="black", width=3)

def draw_testing_circle():
    pos, rad = fd.get_circle_to_draw()
    return canvas.create_oval(pos.x - rad, pos.y - rad,
            pos.x + rad, pos.y + rad, fill="green", width=2)


testing_circle = draw_testing_circle()

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
            fd.step()


    if millis() - last_computation >= cs.UPS_TICK:
        last_computation = millis()
        if running:
            ang = values["-ANGLE-"]
            fd.car.turn(-ang)
            fd.car.push(-values["-FORCE-"]/500)
            fd.step()
        comp_time = millis() - last_computation

    if millis() - last_redraw >= cs.FPS_TICK:
        for item in fd.to_show:
            item.show(canvas)
            
        last_redraw = millis()
        canvas.delete(testing_circle)
        testing_circle = draw_testing_circle()
        draw_time = millis() - last_redraw

    free_time = int(max(0, cs.UPS_TICK - millis() + tick_start))/2

window.close()
