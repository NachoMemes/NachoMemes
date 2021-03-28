import contextlib
from collections import OrderedDict
from typing import Callable, Iterator, TypeVar

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')
class SimpleCache(OrderedDict[_KT, _VT]):
    def __init__(self, max_items:int):
        self.max_items = max_items;

    def __setitem__ (self, key, new_value):
        if len(self) > self.max_items:
            self.popitem(last=False)
        super().__setitem__(key, new_value)


T = TypeVar("T")
def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., contextlib.AbstractContextManager[T]]:
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": contextlib.AbstractContextManager[T]}
    return result