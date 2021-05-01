# dont touch
import PySimpleGUI as sg

COLUMNS = 2

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
class ConfigItem():
    def __init__(self, name, type_):
        self.name = name
        self.type_ = type_
        self.value = NotImplemented

    def get_layout_entry(self):
        return (sg.Text(self.name, size=(15, 1)),
                sg.Input(str(self.value), size=(5, 1)),
                sg.VerticalSeparator())

    def include_in_dict(self, dct):
        dct[self.name] = self.value

    def extract_from_dict(self, dct):
        self.value = dct[self.name] 

test = "fps ups iterations mstep_amount i d k w h a t".split()
all_items = []
for i in test:
    c = ConfigItem(i, None).get_layout_entry()
    all_items.extend(c)

table = list(chunks(all_items, 3*COLUMNS))
layout = table + [[sg.Button("Load"), sg.Button("Save")]]
layout = layout + [[sg.In() ,sg.FileBrowse()]]

window = sg.Window("Config", layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
