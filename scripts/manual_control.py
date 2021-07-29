import time

import pynput
import PySimpleGUI as sg

import viroro.render as render
import utils

CONFIG_FILE = "big_car.toml"
VIEWPORT_SIZE = (1200, 600)

FPS = 100
FRAME_PERIOD = 1/FPS

def create_window():
    viewport = render.Viewport(size=VIEWPORT_SIZE)
    layout = [[
        sg.Frame("Viewport", [[viewport.sg_graph]]),
            sg.Column([
                [sg.B("Reset car", key="-RESET_CAR-")],
                [sg.Checkbox("AI control", key="-AI-")],
                [sg.Frame("Values", [[sg.Text("", size=(50, 10), key="-DEBUG-")]])],
            ])
        ]]
    return (sg.Window("Viroro 🚚", layout, finalize=True), viewport)


def listen_keyboard():
    keys = {"w": False, "a": False, "s": False, "d": False}

    def on_press(key):
        try:
            if key.char in {"w", "a", "s", "d"}:
                keys[key.char] = True
        except AttributeError:
            pass

    def on_release(key):
        try:
            if key.char in {"w", "a", "s", "d"}:
                keys[key.char] = False
        except AttributeError:
            pass

    keyboard_listener = pynput.keyboard.Listener(on_press, on_release)
    keyboard_listener.start()
    return keys


def main():
    sg.theme("Reddit")
    window, viewport = create_window()
    viewport.init_canvas()

    field = utils.create_field(CONFIG_FILE)

    text_box = {"FPS": None}
    keyboard_pressed = listen_keyboard()

    next_frame = time.time()
    fps_counter_start = time.time()
    fps_counter = 0

    while True:
        free_time = max(0, (next_frame-time.time())*1000)
        event, values = window.read(timeout=free_time)

        # GUI events
        if event == sg.WIN_CLOSED:
            break
        elif event == "-RESET_CAR-":
            field.reset()

        # User input
        if keyboard_pressed["w"]:
            user_throttle = +1
        elif keyboard_pressed["s"]:
            user_throttle = -1
        else:
            user_throttle = 0
        if keyboard_pressed["a"]:
            user_steer = -1
        elif keyboard_pressed["d"]:
            user_steer = +1
        else:
            user_steer = 0

        # Simulation
        if time.time() > next_frame:
            next_frame = max(next_frame + FRAME_PERIOD, time.time())

            # Control
            field["car"].apply_control(user_steer, user_throttle)

            # Render
            utils.set_camera_on_car(field, viewport, zoom=200)
            render.draw_field(field, viewport)

            # Compute simulation
            field["pymunk_field"].step()

            fps_counter += 1
            if time.time() > (fps_counter_start + 3):
                text_box["FPS"] = round(fps_counter / (time.time() - fps_counter_start), 1)
                fps_counter_start = time.time()
                fps_counter = 0

            window["-DEBUG-"].update(
                    "\n".join(f"{n}: {v}" for n, v in text_box.items()))


if __name__ == "__main__":
    main()
