import neat
import utils

RUN_STEPS = 300 # Amount of simulation steps for scoring genome

class EvalGenome():
    def __init__(self, genome, neat_config, viroro_config):
        self._id, g = genome
        self.steps_left = RUN_STEPS
        self.wall_hits = 0

        self.field = utils.create_field(viroro_config)
        self.network = create_network(genome, neat_config)
    
    def run(self):
        while self.steps_left:
            self.step()

    def step(self):
        inp = self.field["car"].get_sensor_values()
        out = self.network.activate(inp)
        self.field["car"].control(out[0], out[1])

        self.field.step()

        self.steps_left -= 1
        if self.field.car_hit:
            self.wall_hits += 1
        if self.wall_hits > 40:
            self.steps_left = 0

    def results(self):
        score = self.field["checkpoints"].score() - self.wall_hits * 0.1
        return (self._id, score)


def create_network(genome, neat_config):
    return neat.nn.FeedForwardNetwork.create(genome, neat_config)