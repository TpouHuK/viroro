import pytomlpp

import viroro.physics
from viroro.evolve import NeatChamber, StaticGenome

config = pytomlpp.load("items.toml")
field = viroro.physics.PymunkField(config.field)

MyChamber(config="config-feedforward.txt", field, population)
