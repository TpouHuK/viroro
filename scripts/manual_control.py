import PySimpleGUI as sg

import time

import pytomlpp
import PySimpleGUI as sg
import pynput
import neat

import viroro.physics as ph
import viroro.render as render

FRAME_TIME = 1/60 * 1000
#FRAME_TIME = 1/10 * 1000
FIELD_CONFIG = pytomlpp.load(open("small_car.toml"))
FIELD_STEPS = 100

VIEWPORT_SIZE = (1200, 600)


def millis():
    return int(time.time()*1000)


def create_window():
    viewport = render.Viewport(size=VIEWPORT_SIZE)
    layout = [[
        sg.Frame("Viewport", [[viewport.sg_graph]]),
            sg.Column([
                [sg.B("Reset car", key="-RESET_CAR-")],
                [sg.Checkbox("AI control", key="-AI-")],
                [sg.Frame("Values", [[sg.Text("", size=(50, 10), key="-VALUES-")]])],
            ])
        ]]
    return (sg.Window("Viroro 🚚", layout, finalize=True), viewport)


def create_network(g, config):
    net = neat.nn.FeedForwardNetwork.create(g, config)
    def algo(inp):
        return net.activate(inp)
    return algo


def create_ai_from_checkpoints():
    population = neat.Checkpointer.restore_checkpoint("neat-checkpoint-48")
    config_path = "config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    """
    for ind, g in enumerate(population.population.values()):
        print(f"{ind}/{len(population.population)}")
        a = main_evolve.EvalGenome((None, g), config)
        a.run()
        g.fitness = a.results()[1]
        print(g.fitness)

    max_fit = float("-inf")
    best_genome = None
    best_id = None
    for _id, g in population.population.items():
        if g.fitness >= max_fit:
            max_fit = g.fitness
            best_genome = g
            best_id = _id

    print(f"ID: {best_id}")
    """
    best_genome = population.population[8885]
    net = create_network(best_genome, config)
    return net


def main():
    sg.theme("Reddit")
    window, viewport = create_window()
    viewport.create_draw_options()

    field = ph.Field(FIELD_CONFIG)

    last_frame = 0
    
    text_box = {}
    iddle_gui_time = 0

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

    AVG_LOOP_COUNT = 20
    loop_times = [0] * AVG_LOOP_COUNT
    iddle_times = [0] * AVG_LOOP_COUNT

    net = create_ai_from_checkpoints()
    while True:
        t0 = millis()
        event, values = window.read(timeout=iddle_gui_time)

        if event == sg.WIN_CLOSED:
            break
        elif event == "-RESET_CAR-":
            field.reset()

        # Input
        if keys["w"]:
            gas = 100
        elif keys["s"]:
            gas = -100
        else:
            gas = 0

        if keys["a"]:
            steer = -field.car.max_steer_angle
        elif keys["d"]:
            steer = +field.car.max_steer_angle
        else:
            steer = 0

        a, b = net(field.car.get_sensor_values())
        angle = a * field.car.max_steer_angle
        throttle = b * 100

        if values["-AI-"]:
            field.car.control(throttle, angle)
        else:
            field.car.control(gas, steer)


        # Rendering
        if millis() - last_frame > FRAME_TIME:
            draw_t0 = millis()
            field.step()

            # Camera control
            zoom = 230
            offset = field.car.body.position * -zoom + (VIEWPORT_SIZE[0]/2, VIEWPORT_SIZE[1]/2)
            car_angle = field.car.body.angle
            viewport.set_view(zoom, offset, car_angle)

            viewport.show(field)
            draw_time = millis() - draw_t0

            text_box["vis_car_score"] = round(field.score(), 2)
            text_box["vis_time"] = draw_time

            text_box["avg_loop_time"] = round(sum(loop_times)/AVG_LOOP_COUNT)
            text_box["avg_iddle_time"] = round(sum(iddle_times)/AVG_LOOP_COUNT)
            text_box["car_hit"] = field.car_hit
            text_box["angle"] = round(angle)
            text_box["throttle"] = round(throttle)
            window["-VALUES-"].update(
                    "\n".join(f"{n}: {v}" for n, v in text_box.items()))

        loop_time = millis() - t0
        loop_times.append(loop_time)
        loop_times.pop(0)

        iddle_gui_time = max(0, round(FRAME_TIME - loop_time))
        iddle_times.append(iddle_gui_time)
        iddle_times.pop(0)



if __name__ == "__main__":
    main()
