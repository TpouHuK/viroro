class Brain():
    def __init__(self, name="John"):
        self.name = name

    def compute(self, inp):
        return 0

    @classmethod
    def from_json(cls, json):
        return cls()

    def to_json(self):
        return "{}"

