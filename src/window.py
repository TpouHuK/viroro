import PySimpleGUI as sg
import time
import constants as cs
import physics
import test_items


def millis():
    return int(time.time()*1000)


def create_test_1_window():
    layout = [
        [
            sg.Button("Debug button", key="-DEBUG-"), sg.CBox("AI", key="-AI-")
        ],
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
            sg.Text("TESTING IN PROGRESS", key="-TEXT-", size=(100, 2))
        ],
        [
            sg.Graph(
                cs.FIELD_SIZE_PIXELS, (0, 0), cs.FIELD_SIZE_PIXELS, key="-CANVAS-")
        ],
    ]
    window = sg.Window(cs.WINDOW_TITLE, layout, finalize=True)
    return window


def test_gui_1(p_field, car, checkpoints, to_show, debug):
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
        if not values['-AI-']:
            car.steer(ang)
            car.push(values["-FORCE-"]/1.5)
        else:
            car.algo(car)
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
        elif event == "-DEBUG-":
            debug()

        if millis() - last_calculation >= cs.UPS_TICK:
            last_calculation = millis()
            if running:
                step()
            calc_time = millis() - last_calculation

        if millis() - last_redraw >= cs.FPS_TICK:
            last_redraw = millis()
            for item in to_show:
                item._show(canvas)
            window["-TEXT-"].update(f"calc_time: {calc_time}, draw_time: {draw_time}, car_speed: {round(car.speed*3.6, 2)}, score: {round(checkpoints.get_car_score(0), 2)}")
            draw_time = millis() - last_redraw

    window.close()


def create_evolution_window():
    right_block = [
        [
            sg.Text("", size=(10, 10), key="--OUTPUT--")
        ],
        [
            sg.Button("Start", key="-START-", size=(6, 1)),
            sg.Button("Stop", key="-STOP-", size=(6, 1)),
            sg.Button("Show best", key="-BEST-"),
        ],
        [   sg.Text("Current generation: "),
            sg.ProgressBar(100, orientation='h', size=(51, 10), key='-PROGRESSBAR-')
        ],
        [
            sg.Frame(title="Field", layout=[[
            sg.Graph(
                cs.FIELD_SIZE_PIXELS, (0, 0), cs.FIELD_SIZE_PIXELS, key="-CANVAS-")]])
        ],
    ]

    layout = [[sg.Column(right_block)]]

    window = sg.Window(cs.WINDOW_TITLE, layout, finalize=True)
    return window


def evolution_gui(tcomm):
    window = create_evolution_window()
    canvas = window["-CANVAS-"].TKCanvas

    global last_values
    last_values = [0]*6

    def step(control_fn):
        global last_values
        sensor_values = car.get_sensor_values()
        a, b = control_fn(sensor_values + last_values)
        last_values = sensor_values
        car.steer(a*30)
        car.push(b*100)
        p_field.step()

    free_time = 0
    last_calculation = 0
    last_redraw = 0
    calc_time = 0
    draw_time = 0
    tick_start = 0
    to_show = []
    running = False

    while True:
        free_time = max(0, cs.UPS_TICK - (millis() - tick_start))
        tick_start = millis()
        event, values = window.read(timeout=free_time)

        if event == sg.WIN_CLOSED:
            break
        elif event == "-START-":
            tcomm.evolving.set()
        elif event == "-STOP-":
            tcomm.evolving.clear()
            running = False
        elif event == "-BEST-":
            for item in to_show:
                item._cls(canvas)
            to_show = []
            running = True
            control_fn = tcomm.eval_chamber.get_control_function(
                    tcomm.eval_chamber.population.best_genome
                    )
            p_field = physics.PymunkField()
            car = test_items.car_1((0.5, 3.5), group=1)
            walls = test_items.walls_2()

            p_field.add(car, walls)
            to_show = [car, walls]
            continue #FIXMEEEEEEEEEEEEEEEEEEE

        if millis() - last_calculation >= cs.UPS_TICK:
            last_calculation = millis()
            if running:
                step(control_fn)
            calc_time = millis() - last_calculation

        if millis() - last_redraw >= cs.FPS_TICK:
            last_redraw = millis()
            for item in to_show:
                item._show(canvas)
            window["-PROGRESSBAR-"].update(tcomm.progress)
            draw_time = millis() - last_redraw

    window.close()


sg.theme("Reddit")
