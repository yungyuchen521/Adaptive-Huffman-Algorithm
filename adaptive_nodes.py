from typing import Optional, Set


class BaseNode:
    def __init__(self, id: int, weight: int, parent=None):
        self._id: int = id
        self._weight: int = weight
        self._parent: BaseNode = parent
        self._left: BaseNode = None
        self._right: BaseNode = None

    def __str__(self):
        return f"|{self._parent.id if self._parent else 'NA'}|->|{self._id}|, w={self._weight}"

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
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right
    
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
            return f"{super().__str__()}, order={self._order}, chr={chr(self._order)}"
        else:
            return f"internal: {super().__str__()}"

    @property
    def order(self):
        return self._order

    @property
    def is_symbol(self) -> bool:
        return self._order >= 0

    def set_parent(self, parent):
        assert isinstance(parent, Node)
        self._parent = parent

    def increment_weight(self):
        self._weight += 1

    def set_id(self, id: int):
        self._id = id

class NYT(BaseNode):
    def __init__(self, bits_per_symbol: int):
        super().__init__(id=0, weight=0, parent=None)

        self._bits_per_symbol = bits_per_symbol
        self._nyt_set: Set[int] = set(range(2**bits_per_symbol)) # use the complement to reduce size?

        self._bits_buffer: str = ""

    def __str__(self):
        return f"NYT: {super().__str__()}"

    def set_parent(self, parent: Node):
        assert isinstance(parent, Node)
        self._parent = parent
        self._id = parent.id + 2

    def encode(self, order: int) -> str:
        assert order in self._nyt_set
        self._nyt_set.remove(order)
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
        self._nyt_set.remove(order)

        return chr(order)
