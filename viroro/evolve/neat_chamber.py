from .chamber import Chamber

class NeatChamber(Chamber):
    # This class is not implemented, implement it
    def __init__(self, config_path):
        raise NotImplemented
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

    def run(self, amount_of_generations):
        self.population.run(_eval_fitness, amount_of_generations)

    def get_control_function(self, genome):
        net = neat.nn.FeedForwardNetwork.create(genome, self.config)
        def control(sensor_values):
            output = net.activate(sensor_values)
            return output
        return control

