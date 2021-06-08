import PySimpleGUI as sg

import viroro.render as r
import viroro.physics as ph

FIELD_CONFIG = pytomlpp.load(open("small_car_items.toml"))
field = ph.Field(FIELD_CONFIG)


