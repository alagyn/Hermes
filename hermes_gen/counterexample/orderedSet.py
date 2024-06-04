from typing import TypeVar, Generic, List, Iterator

T = TypeVar("T")


class OrderedSet(Generic[T]):
    """
    Generic set that remembers the order items were added
    Keeps things deterministic when you have a relatively small
    number of items to keep track of
    """

    def __init__(self) -> None:
        self._items: List[T] = []

    def add(self, item: T):
        if item not in self._items:
            self._items.append(item)

    def __contains__(self, item: T) -> bool:
        return item in self._items

    def remove(self, item: T):
        self._items.remove(item)

    def copy(self) -> 'OrderedSet[T]':
        out = OrderedSet()
        out._items = self._items.copy()
        return out

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)
