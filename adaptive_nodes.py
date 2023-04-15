from typing import Optional, Set

from utils import extended_chr


class BaseNode:
    def __init__(self, id: int, weight: int, parent=None):
        self._id: int = id
        self._weight: int = weight
        self._parent: BaseNode = parent
        self._left: BaseNode = None
        self._right: BaseNode = None

        self._depth: int = 0 if parent is None else parent._depth + 1

    def __str__(self):
        # {parent id}->{id}, {weight}, {depth}
        return f"|{self._parent.id if self._parent else 'NA'}|->|{self._id}|, w={self._weight}, d={self._depth}"

    @property
    def id(self):
        return self._id

    @property
    def weight(self):
        return self._weight

    @property
    def parent(self):
        return self._parent

    @property
    def depth(self):
        return self._depth

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right
    
    def update_depth(self):
        self._depth = 0 if self._parent is None else self.parent.depth + 1

    def set_left(self, node):
        assert isinstance(node, BaseNode)
        self._left = node
    
    def set_right(self, node):
        assert isinstance(node, BaseNode)
        self._right = node

    @property
    def order(self):
        raise NotImplementedError

    @property
    def is_symbol(self):
        raise NotImplementedError

class Node(BaseNode):
    def __init__(self, id: int, parent: BaseNode, weight: int, order: int=-1):
        super().__init__(id=id, weight=weight, parent=parent)
        self._order = order

    def __str__(self):
        if self.is_symbol:
            return f"{super().__str__()}, order={self._order}"
        else:
            return f"internal: {super().__str__()}"

    def __lt__(self, node):
        return self._depth < node.depth

    @property
    def order(self):
        return self._order

    @property
    def is_symbol(self) -> bool:
        return self._order >= 0

    def update_weight(self):
        assert not self.is_symbol
        self._weight = self._left.weight + self._right.weight

    def shrink(self, factor: int=2):
        assert self.is_symbol
        assert factor > 1
        self._weight = max(1, self._weight // factor)

    def set_parent(self, parent):
        assert isinstance(parent, Node)
        self._parent = parent
        self._depth = parent.depth + 1

    def increment_weight(self):
        self._weight += 1

class NYT(BaseNode):
    def __init__(self, bits_per_symbol: int):
        super().__init__(id=0, weight=0, parent=None)

        self._bits_per_symbol = bits_per_symbol
        self._transmitted_set: Set[int] = set()

        self._bits_buffer: str = ""

    def __str__(self):
        return f"NYT: {super().__str__()}"

    def set_parent(self, parent: Node):
        assert isinstance(parent, Node)
        self._parent = parent

    def encode(self, order: int) -> str:
        assert order not in self._transmitted_set
        self._transmitted_set.add(order)
        return self._order_to_bin_str(order)

    def decode(self, bit: str) -> Optional[str]:
        assert bit == "0" or bit == "1"

        self._bits_buffer += bit
        return (
            self._flush_buffer()
            if self._buffer_full()
            else None
        )

    def _order_to_bin_str(self, order: int) -> str:
        bin_str = bin(order).split("b")[-1]
        return (self._bits_per_symbol - len(bin_str)) * "0" + bin_str

    def _buffer_full(self) -> bool:
        assert len(self._bits_buffer) <= self._bits_per_symbol
        return len(self._bits_buffer) == self._bits_per_symbol

    def _flush_buffer(self) -> str:
        assert len(self._bits_buffer) == self._bits_per_symbol

        order = 0

        for bit in self._bits_buffer:
            assert bit in "01"

            order <<= 1
            if bit == "1":
                order += 1

        self._bits_buffer = ""
        self._transmitted_set.add(order)

        return extended_chr(order, self._bits_per_symbol)
