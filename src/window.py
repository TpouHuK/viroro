import PySimpleGUI as sg
import time
import constants as cs


def millis():
    return int(time.time()*1000)


def create_test_1_window():
    layout = [
        [
            sg.Text("Angle", size=(6, 1)),
            sg.Slider(range=(-45, 45), default_value=0, orientation="h", key="-ANGLE-")
        ],
        [
            sg.Text("Thrust", size=(6, 1)),
            sg.Slider(range=(-100, 100), default_value=0, orientation="h", key="-FORCE-")
        ],
        [
            sg.Button("Run", key="-PAUSE-", size=(6, 1)),
            sg.Button("One step", key="-STEP-", size=(6, 1))
        ],
        [
            sg.Text("TESTING IN PROGRESS", key="-TEXT-", size=(50, 2))
        ],
        [
            sg.Graph(
                cs.FIELD_SIZE_PIXELS, (0, 0), cs.FIELD_SIZE_PIXELS, key="-CANVAS-")
        ],
    ]
    window = sg.Window(cs.WINDOW_TITLE, layout, finalize=True)
    return window


def test_gui_1(p_field, car, to_show):
    window = create_test_1_window()
    canvas = window["-CANVAS-"].TKCanvas

    free_time = 0
    last_calculation = 0
    last_redraw = 0
    calc_time = 0
    draw_time = 0
    tick_start = 0

    def step():
        ang = values["-ANGLE-"]
        car.turn(-ang)
        car.push(-values["-FORCE-"]/1.5)
        p_field.step()

    running = False
    while True:
        free_time = max(0, cs.UPS_TICK - (millis() - tick_start))
        tick_start = millis()
        event, values = window.read(timeout=free_time)

        if event == sg.WIN_CLOSED:
            break
        elif event == "-PAUSE-":
            running = not running
            window["-PAUSE-"].update("Pause" if running else "Run")
        elif event == "-STEP-":
            step()

        if millis() - last_calculation >= cs.UPS_TICK:
            last_calculation = millis()
            if running:
                step()
            calc_time = millis() - last_calculation

        if millis() - last_redraw >= cs.FPS_TICK:
            last_redraw = millis()
            for item in to_show:
                item._show(canvas)
            window["-TEXT-"].update(f"cacl_time: {calc_time}, draw_time: {draw_time}")
            draw_time = millis() - last_redraw

    window.close()


sg.theme("Reddit")
to_show = []
