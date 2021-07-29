import neat
import main_evolve

import pytomlpp
import viroro.physics as physics


def create_field(config_file):
    config = pytomlpp.load(open(config_file))
    car = physics.Car(config["car"])
    walls = physics.Walls(**config["walls"])
    checkpoints = physics.Checkpoints(**config["checkpoints"])

    dt = 1/config["pymunk_field"]["control_ups"]
    microsteps = int(dt*config["pymunk_field"]["simulation_ups"])
    pymunk_field = physics.PymunkField(dt, microsteps)
    pymunk_field.add(car, walls, checkpoints)

    return {
        "car": car,
        "walls": walls,
        "checkpoints": checkpoints,
        "pymunk_field": pymunk_field
        }


def eval_fitness_of_population(population, config):
    for ind, g in enumerate(population.population.values()):
        print(f"{ind}/{len(population.population)}")
        a = main_evolve.EvalGenome((None, g), config)
        a.run()
        g.fitness = a.results()[1]


def find_best_genome_id(population):
    max_fit = float("-inf")
    best_id = None
    for _id, g in population.population.items():
        if g.fitness >= max_fit:
            max_fit = g.fitness
            best_id = _id
    return best_id


def create_network_from_checkpoints(checkpoint_path, config_path, best_id = None):
    population = neat.Checkpointer.restore_checkpoint(checkpoint_path)
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    if not best_id:
        eval_fitness_of_population(population, config)
        best_id = find_best_genome_id(population)
        print(f"Best genome ID: {best_id}")

    best_genome = population.population[best_id]
    network = create_network(best_genome, config)
    return network


def set_camera_on_car(field, viewport, zoom=200):
    offset = field["car"].body.position * -zoom + (viewport.size[0]/2, viewport.size[1]/2)
    car_angle = field["car"].body.angle
    viewport.set_view(zoom, offset, car_angle)