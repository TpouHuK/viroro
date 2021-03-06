import time
import threading
import multiprocessing
import itertools

import pytomlpp
import PySimpleGUI as sg
import neat

import viroro.physics as ph
import viroro.render as render


FRAME_TIME = 1/60 * 1000
FIELD_CONFIG = pytomlpp.load(open("big_car.toml"))
FIELD_STEPS = 600
VIEWPORT_SIZE = (1200, 600)


def millis():
    return int(time.time()*1000)


def create_window():
    viewport = render.Viewport(size=VIEWPORT_SIZE)
    layout = [[
        sg.Frame("Viewport", [[viewport.sg_graph]]),
            sg.Column([
                [sg.B("Run", key="-STARTSTOP-", size=(5,1))],
                [sg.ProgressBar(100, "horizontal", size=(34, 10), key="-PROGRESS-")],
                [sg.B("Dump"), sg.B("Load"), sg.B("Reset best car view", key="-RESET_BEST_CAR-")],
                [sg.Frame("Values", [[sg.Text("", size=(50, 10), key="-VALUES-")]])],
                [sg.Frame("Fitness eval", [
                    [sg.Radio("Solo", 1, key="-SOLO-", default=True)],
                    [sg.Radio("With circles", 1, key="-CIRCLES-")],
                    [sg.Radio("With PID-bots", 1, key="-PID_BOTS-")],
                    [sg.Radio("With population", 1, key="-POP_BOTS-")],
                ])],
                [sg.Frame("Visualisator", [
                    [sg.Radio("None", 2, key="-VIS_MODE_NONE-", default=True)],
                    [sg.Radio("Show best of previous gen", 2, key="-VIS_MODE_BEST-")],
                    [sg.Radio("Full visualisation", 2, key="-VIS_MODE_FULL-")],
                ])],
            ])
        ]]
    window = sg.Window("Viroro 🚚", layout, finalize=True)
    viewport.create_draw_options()
    return (window, viewport)


def create_testing_chamber(g, config):
    net = neat.nn.FeedForwardNetwork.create(g, config)

    def algo(inp):
        return net.activate(inp)

    fd = ph.Field(FIELD_CONFIG)
    fd.algo = algo
    return fd


send_frames = False
cur_frame = []
cur_frame_lock = threading.Lock()
cur_frame_ready = threading.Event()
cur_progress = 0
cur_generation = 0
cur_max_fitness = 0

best_field = None
best_field_lock = threading.Lock()

class EvalGenome():
    def __init__(self, genome, config):
        self._id, g = genome
        self.steps_left = FIELD_STEPS
        self.field = create_testing_chamber(g, config)
        self.wall_hits = 0
    
    def run(self):
        while self.step():
            pass

    def step(self):
        if self.steps_left:
            self.field.step()
            self.steps_left -= 1
            if self.field.car_hit:
                self.steps_left = 0
                self.wall_hits += 1
            if self.wall_hits > 40:
                self.steps_left = 0
        return bool(self.steps_left)

    def results(self):
        score = self.field.score() - self.wall_hits * 0.1
        return (self._id, score)


def _eval_genome(arg):
    chamber = EvalGenome(*arg)
    chamber.run()
    return chamber.results()


def calc_thread(popul):
    global cur_frame
    global cur_frame_lock
    global cur_frame_ready
    global send_frames
    global cur_progress
    global cur_generation
    global best_field
    global cur_max_fitness

    cur_progress = 0
    if not send_frames:
        def _eval_fitness(genomes, config):
            global cur_progress
            with multiprocessing.Pool() as p:
                fitnesses = {}
                for _id, fit in p.imap_unordered(_eval_genome, zip(genomes, itertools.repeat(config))):
                    fitnesses[_id] = fit
                    cur_progress = len(fitnesses)/len(genomes)*100
                for _id, genome in genomes:
                    genome.fitness = fitnesses[_id]
    else:
        def _eval_fitness(genomes, config):
            global cur_progress
            global cur_frame
            chambers = []
            for genome in genomes:
                chambers.append(EvalGenome(genome, config))

            cur_frame = chambers
            active_chambers = chambers.copy()

            cur_step = 0
            while active_chambers:
                cur_frame_ready.wait()
                with cur_frame_lock:
                    active_chambers = list(filter(lambda x: x.step(), active_chambers))
                cur_frame_ready.clear()
                steps_done = (len(chambers)-len(active_chambers))*FIELD_STEPS + len(active_chambers)*cur_step
                all_steps = len(chambers)*FIELD_STEPS
                cur_progress = steps_done/all_steps*100
                cur_step += 1
                
            for chamber, genome in zip(chambers, genomes):
                genome[1].fitness = chamber.results()[1]

    popul.run(_eval_fitness, 1)
    cur_generation = popul.generation

    with cur_frame_lock:
        cur_frame = []
        cur_frame_ready.set()

    with best_field_lock:
        if popul.best_genome.fitness > cur_max_fitness:
            best_field = create_testing_chamber(popul.best_genome, popul.config)
            cur_max_fitness = popul.best_genome.fitness


def main(population, config):
    global cur_frame
    global cur_frame_lock
    global cur_frame_ready
    global send_frames
    global cur_progress
    global cur_generation
    global best_field

    sg.theme("Reddit")
    window, viewport = create_window()
    
    evolving_population = False

    best_field = ph.Field(FIELD_CONFIG)
    best_field.algo = lambda x: (30, -50)

    evolving_thread = threading.Thread(target=calc_thread, args=(), daemon=True)
    last_frame = 0

    last_vis_mode = "-VIS_MODE_NONE-"
    
    text_box = {}
    text_box["iddle_gui_time"] = 0
    text_box["loop_time"] = 0
    text_box["vis_time"] = 0
    text_box["vis_car_score"] = 0
    text_box["since_starting_gen"] = millis() + 9000
    text_box["generation"] = 0
    iddle_gui_time = 0
    gen_start = 0

    while True:
        t0 = millis()
        event, values = window.read(timeout=iddle_gui_time)

        if event == sg.WIN_CLOSED:
            break
        elif event == "-STARTSTOP-":
            evolving_population = not evolving_population
            window['-STARTSTOP-'].update("Run" if not evolving_population else "Stop")
        elif event == "-RESET_BEST_CAR-":
            with best_field_lock:
                best_field.reset()

        # Evolving
        if evolving_population and not evolving_thread.is_alive():
            evolving_thread = threading.Thread(target=calc_thread, args=(population,), daemon=True)
            evolving_thread.start()
            gen_start = millis()

        # Drawing
        if millis() - last_frame > FRAME_TIME:
            draw_t0 = millis()
            window["-PROGRESS-"].update(cur_progress)
            if values["-VIS_MODE_NONE-"]:
                cur_mode = "-VIS_MODE_NONE-"
            elif values["-VIS_MODE_FULL-"]:
                cur_mode = "-VIS_MODE_FULL-"
            elif values["-VIS_MODE_BEST-"]:
                cur_mode = "-VIS_MODE_BEST-"
            send_frames = cur_mode == "-VIS_MODE_FULL-"
            if cur_mode != last_vis_mode:
                #viewport.canvas.delete("all")
                pass
            last_vis_mode = cur_mode
            if not values["-VIS_MODE_FULL-"] and not cur_frame_ready.is_set():
                cur_frame_ready.set()
            if values["-VIS_MODE_FULL-"]:
                if not cur_frame_ready.is_set():
                    with cur_frame_lock:
                        if cur_frame:
                            viewport.show(cur_frame[0].field)
                            for chamber in cur_frame[1:]:
                                viewport.show_car(chamber.field.car)
                        else:
                            pass
                            #viewport.canvas.delete("all")
                        cur_frame_ready.set()
            elif values["-VIS_MODE_BEST-"]:
                with best_field_lock:
                    #viewport.canvas.delete("all")
                    viewport.show(best_field)
                    best_field.step()
                    text_box["vis_car_score"] = round(best_field.score(), 2)

            draw_time = millis() - draw_t0
            text_box["vis_time"] = draw_time
            text_box["since_starting_gen"] = round((millis() - gen_start) / 1000)

        loop_time = millis() - t0
        iddle_gui_time = max(0, round(FRAME_TIME - loop_time))
        text_box["iddle_gui_time"] = iddle_gui_time
        text_box["loop_time"] = round(loop_time)
        text_box["generation"] = cur_generation

        window["-VALUES-"].update(
                "\n".join(f"{n}: {v}" for n, v in text_box.items()))


if __name__ == "__main__":
    config_path = "config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Create core evolution algorithm class
    population = neat.Population(config)
    #population = neat.Checkpointer.restore_checkpoint("neat-checkpoint-48")


    # Add reporter for fancy statistical result
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    population.add_reporter(neat.Checkpointer(25, 900))

    main(population, config)
