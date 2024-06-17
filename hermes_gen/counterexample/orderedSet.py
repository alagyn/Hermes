from typing import TypeVar, Generic, List, Iterator, Set

T = TypeVar("T")


class OrderedSet1(Generic[T]):
    """
    Just a normal set
    """

    def __init__(self) -> None:
        self._items: Set[T] = set()

    def add(self, item: T):
        self._items.add(item)

    def __contains__(self, item: T) -> bool:
        return item in self._items

    def remove(self, item: T):
        self._items.remove(item)

    def copy(self) -> 'OrderedSet1[T]':
        out = OrderedSet1()
        out._items = self._items.copy()
        return out

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, set) and not isinstance(o, OrderedSet1):
            return False

        if len(self) != len(o):
            return False

        for x in self._items:
            if x not in o:
                return False

        return True


class OrderedSet2(Generic[T]):
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

    def copy(self) -> 'OrderedSet2[T]':
        out = OrderedSet2()
        out._items = self._items.copy()
        return out

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, set) and not isinstance(o, OrderedSet2):
            return False

        if len(self) != len(o):
            return False

        for x in self._items:
            if x not in o:
                return False

        return True

    def __repr__(self) -> str:
        out = "{"
        first = True
        for x in self:
            if not first:
                out += ", "

            out += repr(x)
            first = False

        return out + "}"


OrderedSet = OrderedSet2
