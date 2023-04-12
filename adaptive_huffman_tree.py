from typing import Dict, Optional, Set

from utils import BITS_PER_BYTE


class BaseNode:
    def __init__(self, id: int, weight: int, parent=None):
        self._id: int = id
        self._weight: int = weight
        self._parent: BaseNode = parent
        self._left: BaseNode = None
        self._right: BaseNode = None

    def __str__(self):
        return f"id={self._id}, w={self._weight}, pid={self._parent.id if self._parent else 'NA'}"

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
        return f"{super().__str__()}, order={self._order}"

    @property
    def order(self):
        return self._order

    @property
    def is_symbol(self) -> bool:
        return self._order >= 0

class NYT(BaseNode):
    def __init__(self, bits_per_symbol: int):
        super().__init__(id=0, weight=0, parent=None)

        self._bits_per_symbol = bits_per_symbol
        self._nyt_set: Set[int] = set(range(2**bits_per_symbol)) # use the complement to reduce size?

        self._bits_buffer: str = ""

    def __str__(self):
        return f"NYT: {super().__str__()}"

    def set_parent(self, parent: Node):
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

class AdaptiveHuffmanTree:
    def __init__(self, bytes_per_symbol: int):
        self._bytes_per_symbol: int = bytes_per_symbol
        self._bits_per_symbol: int = bytes_per_symbol * BITS_PER_BYTE

        self._nyt: NYT = NYT(self._bits_per_symbol)
        self._root: BaseNode = self._nyt

        # for encoder
        self._ord_node_dict: Dict[int, BaseNode]  = {}

        # for decoder
        self._cur: BaseNode = self._root
    
    def __str__(self):
        queue = [self._root]
        
        s = ""
        while queue:
            n = queue.pop(0)
            s += f"[{str(n)}]"

            if n.left:
                queue.append(n.left)
                queue.append(n.right)

        return s

    def encode(self, symbol: str) -> str:
        order = ord(symbol)
        node = self._ord_node_dict.get(order)

        if node is None:
            code = self._encode_new_symbol(order)
            self._update(self._nyt)
        else:
            code = self._encode_existing_symbol(node)
            self._update(node)

        return code

    def decode(self, bit: str) -> Optional[str]:
        # every time a non-null symbol is returned
        # self._cur should be set to self._root

        assert bit == "0" or bit == "1"

        if isinstance(self._cur, NYT):
            symbol = self._nyt.decode(bit)

            if symbol is not None:
                self._create_new_node(ord(symbol))
                self._cur = self._root

            return symbol

        self._cur = (
            self._cur.left
            if bit == "0"
            else self._cur.right
        )

        if isinstance(self._cur, NYT) or not self._cur.is_symbol:
            return None
        else:
            symbol = chr(self._cur.order)
            self._cur = self._root
            return symbol

    def _encode_new_symbol(self, order: int) -> str:
        code = self._encode_existing_symbol(self._nyt) + self._nyt.encode(order)
        self._create_new_node(order)
        return code

    def _encode_existing_symbol(self, node: BaseNode) -> str:
        code = ""

        while node.parent is not None:
            if node == node.parent.left:
                code = "0" + code
            elif node == node.parent.right:
                code = "1" + code
            else:
                raise AssertionError(str(node))

            node = node.parent

        return code

    def _create_new_node(self, order: int):
        new_internal = Node(
            id=self._nyt.id,
            parent=self._nyt.parent,
            weight=1,
        )
        if new_internal.parent is None:
            self._root = new_internal
        else:
            new_internal.parent.set_left(new_internal)

        new_node = Node(
            id=self._nyt.id+1,
            parent=new_internal,
            weight=1,
            order=order,
        )
        self._ord_node_dict[order] = new_node

        new_internal.set_left(self._nyt) # update weight?
        new_internal.set_right(new_node) # update weight?
        self._nyt.set_parent(new_internal)

    def _update(self, node: BaseNode):
        self._cur = self._root
