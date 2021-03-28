from collections import OrderedDict

class SimpleCache(OrderedDict):
    def __init__(self, max_items:int):
        self.max_items = max_items;

    def __setitem__ (self, key, new_value):
        if len(self) > self.max_items:
            self.popitem(last=False)
        super().__setitem__(key, new_value)


