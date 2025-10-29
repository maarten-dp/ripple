from ..utils import UInt16


class IdGenerator:
    def __init__(self):
        self.id = UInt16(-1)

    def __call__(self):
        self.id += 1
        return self.id
