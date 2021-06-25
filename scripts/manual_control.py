import time
import threading
import multiprocessing
import itertools

import pytomlpp
import PySimpleGUI as sg
import pynput

import viroro.physics as ph


FRAME_TIME = 1/60 * 1000
FIELD_CONFIG = pytomlpp.load(open("items.toml"))
FIELD_STEPS = 100


def millis():
    return int(time.time()*1000)


def create_window():
    vp_size = (800, 400)
    viewport = sg.Graph(vp_size, (0, 0), vp_size, key="-VIEWPORT-")
    layout = [[
        sg.Frame("Viewport", [[viewport]]),
            sg.Column([
                [sg.B("Dump"), sg.B("Load"), sg.B("Reset car", key="-RESET_CAR-")],
                [sg.Frame("Values", [[sg.Text("", size=(50, 10), key="-VALUES-")]])],
            ])
        ]]
    return sg.Window("Viroro 🚚", layout, finalize=True)


send_frames = False
cur_frame = []
cur_frame_lock = threading.Lock()
cur_frame_ready = threading.Event()
cur_progress = 0
cur_generation = 0
cur_max_fitness = 0

field = None
field_lock = threading.Lock()


def main():
    global field

    sg.theme("Reddit")
    window = create_window()
    
    viewport = ph.DrawOptions(window["-VIEWPORT-"].TKCanvas, 84, (5, 5))
    viewport_items = []
    evolving_population = False

    field = ph.Field(pytomlpp.load(open("items.toml")))

    last_frame = 0
    
    text_box = {}
    text_box["iddle_gui_time"] = 0
    text_box["loop_time"] = 0
    text_box["vis_time"] = 0
    text_box["vis_car_score"] = 0
    text_box["generation"] = 0
    iddle_gui_time = 0
    gen_start = 0

    keys = {"w": False, "a": False, "s": False, "d": False}

    def on_press(key):
        if key.char in {"w", "a", "s", "d"}:
            keys[key.char] = True

    def on_release(key):
        if key.char in {"w", "a", "s", "d"}:
            keys[key.char] = False

    keyboard_listener = pynput.keyboard.Listener(on_press, on_release)
    keyboard_listener.start()

    while True:
        t0 = millis()
        event, values = window.read(timeout=iddle_gui_time)

        if event == sg.WIN_CLOSED:
            break
        elif event == "-RESET_CAR-":
            with field_lock:
                field.reset()

        # Input
        if keys["w"]:
            field.car.push(10)
        elif keys["s"]:
            field.car.push(-10)
        else:
            field.car.push(0)

        if keys["a"]:
            field.car.steer(-field.car.max_steer_angle)
        elif keys["d"]:
            field.car.steer(+field.car.max_steer_angle)
        else:
            field.car.steer(0)


        # Drawing
        if millis() - last_frame > FRAME_TIME:
            draw_t0 = millis()
            draw_time = millis() - draw_t0

            viewport.canvas.delete("all")
            field.show(viewport)
            field.step()
            text_box["vis_car_score"] = round(field.score(), 2)

            text_box["vis_time"] = draw_time

        loop_time = millis() - t0
        iddle_gui_time = max(0, round(FRAME_TIME - loop_time))
        text_box["iddle_gui_time"] = iddle_gui_time
        text_box["loop_time"] = round(loop_time)
        text_box["keys"] = keys

        window["-VALUES-"].update(
                "\n".join(f"{n}: {v}" for n, v in text_box.items()))


if __name__ == "__main__":
    main()
