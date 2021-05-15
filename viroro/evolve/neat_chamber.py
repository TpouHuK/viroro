from .chamber import Chamber

class GenomeDriver():
    def __inif__(self, genome, config)
        net = neat.nn.FeedForwardNetwork.create(genome, config)

    def get_control_function(self, genome):
        def control(sensor_values):
            output = net.activate(sensor_values)
            return output
        return control


class NeatChamber(Chamber):
    def __init__(self, config_path):
        # Set configuration file
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)


        # Create core evolution algorithm class
        self.population = neat.Population(config)

        # Add reporter for fancy statistical result
        self.population.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.population.add_reporter(stats)
        self.config = config

    def run(self, genome_fitness_func, amount_of_generations=1):
        self.population.run(eval_fitness_func, amount_of_generations)
