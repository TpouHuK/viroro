import time

import neat
import pynput
import PySimpleGUI as sg

import viroro.render as render
import utils

FPS = 60
FRAME_PERIOD = 1/FPS
CONFIG_FILE = "big_car.toml"
VIEWPORT_SIZE = (1200, 600)


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
    viewport.create_draw_options()

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
            utils.draw_field(field, viewport)

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
