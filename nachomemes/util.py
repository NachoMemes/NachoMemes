from collections import OrderedDict
from typing import Callable, Iterator, TypeVar, Optional, Iterable
from itertools import chain, takewhile

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')
_T = TypeVar('_T')
Predicate = Callable[[_T], object]

class SimpleCache(OrderedDict[_KT, _VT]):
    def __init__(self, max_items:int):
        self.max_items = max_items;

    def __setitem__ (self, key, new_value):
        if len(self) > self.max_items:
            self.popitem(last=False)
        super().__setitem__(key, new_value)

def pop_arg(text: str) -> tuple[str, Optional[str]]:
    result = text.split(maxsplit=1)
    return result[0], result[1] if len(result) == 2 else None

def partition_on(pred: Predicate[_T], seq: Iterable[_T]) -> Iterable[Iterable[_T]]:
    "Split a sequence into multuple sub-sequences using a provided value as the boundary"
    i = iter(seq)
    while True:
        # note that we need to do an explicit StopIteration check because
        # takewhile returns an empty sequence if it encounters StopIteration
        try:
            n = next(i)
        except StopIteration:
            return
        # return the next sub-sequence up to the boundary.
        yield takewhile(lambda v: not pred(v), chain([n], i))


def partition_on_value(value: _T, seq: Iterable[_T]) -> Iterable[Iterable[_T]]:
    return partition_on(lambda v: v == value, seq)

def partition_on_values(values: list[_T], seq: Iterable[_T]) -> Iterable[Iterable[_T]]:
    return partition_on(lambda v: v in values, seq)
