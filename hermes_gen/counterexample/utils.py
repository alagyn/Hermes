from typing import Deque, TypeVar
import itertools
from collections import deque

T = TypeVar('T')


def sliceDeque(d: Deque[T], start, end) -> Deque[T]:
    return deque(itertools.islice(d, start, end))
