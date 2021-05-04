from window import create_test_1_window, millis
import physics
from math import sqrt
from test_items import car_1, walls_2
import neat
import PySimpleGUI as sg
import constants as cs


def algo(car):
    sensors = car.get_sensor_values()
    p = sensors[2] - sensors[3]
    spd = 20
    car.steer(p*100)
    car.push(spd)


generation = 0
running = False

'''
def debug():
    #car.sensors[0].make_reading()
    print(round(car.sensors[0].read_distance()*100, 2))
'''


def run_car(genomes, config):
    # Init NEAT
    nets = []
    cars = {}

    p_fields = {}
    walls_big = walls_2()

    def _get_checkpoints():
        return physics.CheckPoints(
            [
                (0.5, 2.5),
                (1.5, 0.5),
                (2.5, 1.5),
                (3.5, 2.5),
                (4.5, 1.5),
                (5.5, 0.5),
                (6.5, 1.5),
                (7.5, 2.5),
                (8.5, 3.0),
                (7.5, 3.5),
                (1.5, 3.5),
            ],
            detection_radius=0.5)

    checkpoints_cars = {}

    crutch = {}
    i = 0
    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        # Init my cars
        cars.setdefault(id, car_1(position=(0.5, 3.5), group=1))
        p_fields.setdefault(id, physics.PymunkField())
        walls = walls_2()
        checkpoints_cars.setdefault(id, _get_checkpoints())
        checkpoints_cars[id].add_car(cars[id])
        p_fields[id].add(*[cars[id], walls, checkpoints_cars[id]])
        crutch.setdefault(id, i)
        i += 1

    to_show = [walls_big] + list(cars.values()) + [_get_checkpoints()]

    # window = create_test_1_window()
    global window
    canvas = window["-CANVAS-"].TKCanvas
    free_time = 0
    last_calculation = 0
    last_redraw = 0
    calc_time = 0
    draw_time = 0
    tick_start = 0

    global generation
    generation += 1
    global running
    start_time = millis()
    last_score = [0 for _ in cars]
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
            print("I won't use it")
        elif event == "-DEBUG-":
            print("I won't use it")

        if millis() - last_calculation >= cs.UPS_TICK:
            last_calculation = millis()
            if running:
                # Input my data and get result from network
                for index, car in list(cars.items()):
                    output = nets[crutch[index]].activate(car.get_sensor_values())
                    car.steer(round(output[0]*30))
                    car.push(round(output[1]*100))

                # Update car and fitness
                score = []
                fits = []
                remain_cars = 0
                for i, car in list(cars.items()):
                    if car.get_alive():
                        remain_cars += 1
                        genomes[crutch[i]][1].fitness += (checkpoints_cars[i].get_car_score(0) - last_score[crutch[i]])
                        fits.append(genomes[crutch[i]][1].fitness)
                        score.append(checkpoints_cars[i].get_car_score(0))
                        p_fields[i].step()

                last_score = score

                # check
                if (remain_cars == 0) or ((millis()-start_time) > 60000):
                    break

                calc_time = millis() - last_calculation

                last_redraw = millis()
                for item in to_show:
                    item._show(canvas)
                window["-TEXT-"].update(
                    f"calc_time: {calc_time}, draw_time: {draw_time}, "
                    f"time: {millis()-start_time}, max_score: {max(score)}, "
                    f"generation: {generation}, max_fitness: {max(fits)}")
                draw_time = millis() - last_redraw

    for item in cars.values():
        item.remove(canvas)

#window.test_gui_1(p_field, car, checkpoints, items, debug)

if __name__ == "__main__":
    # Set configuration file
    config_path = "../../viroro/src/config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Create core evolution algorithm class
    p = neat.Population(config)

    # Add reporter for fancy statistical result
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run NEAT
    window = create_test_1_window()
    p.run(run_car, 1000)
