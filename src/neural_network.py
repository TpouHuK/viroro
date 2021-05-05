def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class FFLayer():
    def __init__(self, isize, osize, weights, biases, calc_func):
        self.isize = isize
        self.osize = osize
        self.calc_func = calc_func

    def calculate(self, inp):
        assert len(inp) == self.isize

        output = []
        for layer_w, b in (self.weight, self.biases):
            t_o = self.calc_func(sum(i*w for i, w in zip(inp, layer_w)) + b)
            output.append(t_o)
            
        return output

    def flatten(self):
        return sum(self.weights) + self.biases

    @classmethod
    def from_init_func(cls, isize, osize, init_func, calc_func):
        weights = [[init_func() for _ in range(isize)] for _ in range(osize)]
        biases = [init_func() for _ in range(osize)]

        return cls(isize, osize, weights, biases, calc_func)

    @classmethod
    def from_flatten(cls, isize, osize, flatten, calc_func):
        assert len(flatten) = isize*osize + osize
        weights = list(chunks(flatten[:isize*osize], isize))
        biases = flatten[isize*osize:]
        return cls(isize, osize, weights, biases, calc_func)
        

class FFNeuralNetwork():
    def __init__(self, input_size, output_size, hidden_layers=(3,)):
        temp_list = [input_size, *hidden_layers, output_size]
