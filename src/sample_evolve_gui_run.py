from window import evolution_gui
import neat_evolution
import threading
from time import sleep


class ThreadCommunication():
    def __init__(self):
        self.progress = 0
        self.evolving = threading.Event()
        self.eval_chamber = None


def thread1(tcomm):
    evolution_gui(tcomm)
    pass


def thread2(tcomm):
    tcomm.eval_chamber = neat_evolution.EvolutionChamber()
    while True:
        tcomm.evolving.wait()
        while tcomm.evolving.is_set():
            tcomm.progress = 50
            eval_chamber.run(1)
            tcomm.progress = 100


a = ThreadCommunication()
threading.Thread(target=thread1, args=(a,)).start()
threading.Thread(target=thread2, args=(a,), daemon=True).start()
