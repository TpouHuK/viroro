# REWRITE ME:
# STATUS: GARBAGE
# TOO MUCH OF HARDCODED THINGS
# TYVM FOR TEST_ITEMS

import neat
import physics
from test_items import car_1, walls_2, checkpoints_2
from multiprocessing import Pool
import itertools

RUN_TICKS = 600


def _eval_genome(genome, config):
    genome = genome[1]
    car = car_1(position=(0.5, 3.5), group=1)
    p_field = physics.PymunkField()
    walls = walls_2()
    checkpoints = checkpoints_2()
    checkpoints.add_car(car)
    p_field.add(car, walls, checkpoints)
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    last_sensors = [0]*6
    for _ in range(RUN_TICKS):
        sensors = car.get_sensor_values()
        output = net.activate(sensors + last_sensors)
        last_sensors = sensors
        car.steer(round(output[0]*45))
        car.push(round(output[1]*100))
        p_field.step()
    return checkpoints.get_car_score(idx=0)


def _eval_fitness(genomes, config):
    with Pool() as p:
        fitnesses = p.starmap(
                _eval_genome,
                zip(genomes, itertools.repeat(config)))
        
    for fitness, raw_genome in zip(fitnesses, genomes):
        id_, genome = raw_genome
        genome.fitness = fitness


class EvolutionChamber():
    def __init__(self):
        # Set configuration file
        config_path = "config-feedforward.txt"
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)


        # Create core evolution algorithm class
        self.population = neat.Population(config)

        # Add reporter for fancy statistical result
        self.population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.population.add_reporter(stats)
        self.config = config

    def run(self, amount_of_generations):
        self.population.run(_eval_fitness, amount_of_generations)

    def get_control_function(self, genome):
        net = neat.nn.FeedForwardNetwork.create(genome, self.config)
        def control(sensor_values):
            output = net.activate(sensor_values)
            return output
        return control

if __name__ == "__main__":
    EvolutionChamber().run(10)