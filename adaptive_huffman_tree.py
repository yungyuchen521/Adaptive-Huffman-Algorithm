from typing import Dict, List, Optional, Tuple
from math import log2

from utils import BITS_PER_BYTE, extended_chr, extended_ord
from adaptive_nodes import BaseNode, Node, NYT


class AdaptiveHuffmanTree:
    def __init__(self, bytes_per_symbol: int):
        self._bytes_per_symbol: int = bytes_per_symbol
        self._bits_per_symbol: int = bytes_per_symbol * BITS_PER_BYTE

        self._symbol_cnt: int = 0

        self._nyt: NYT = NYT(self._bits_per_symbol)
        self._root: BaseNode = self._nyt

        # for encoder
        self._ord_node_dict: Dict[int, Node]  = {}

        # for decoder
        self._cur: BaseNode = self._root
    
    @property
    def entropy(self) -> float:
        ent = 0
        stack = [self._root]

        while stack:
            node = stack[-1]
            if isinstance(node, Node) and node.is_symbol:
                p = node.weight / self._symbol_cnt
                ent -= p * log2(p)

            if node.left:
                stack.append(node.left)
                stack.append(node.right)

        return ent

    def __str__(self):
        # (depth, Node)
        queue: List[Tuple[int, BaseNode]] = [(0, self._root)]
        
        s = ""
        depth = 0
        while queue:
            d, n = queue.pop(0)

            if d > depth:
                assert depth+1 == d
                s += "\n"
                depth = d
            
            s += f"[{str(n)}] "

            if n.left:
                queue.append((d+1, n.left))
                queue.append((d+1, n.right))

        return s

    def encode(self, symbol: str) -> str:
        self._symbol_cnt += 1
        order = extended_ord(symbol)
        node = self._ord_node_dict.get(order)

        if node is None:
            code = self._encode_new_symbol(order)
            # tree updated in create_new_node
        else:
            code = self._encode_existing_symbol(node)
            self._update(node)

        return code

    def decode(self, bit: str) -> Optional[str]:
        # whenever a non-null symbol returned
        # self._cur should be set to self._root

        assert bit == "0" or bit == "1"

        if isinstance(self._cur, NYT):
            symbol = self._nyt.decode(bit)

            if symbol is not None:
                self._create_new_node(extended_ord(symbol))
                # tree updated in create_new_node
                self._cur = self._root

            return symbol

        self._cur = (
            self._cur.left
            if bit == "0"
            else self._cur.right
        )

        if isinstance(self._cur, Node) and self._cur.is_symbol:
            symbol = extended_chr(self._cur.order, self._bits_per_symbol)
            self._update(self._cur)
            self._cur = self._root
            return symbol
        else:
            return None

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

        new_internal.set_left(self._nyt)
        new_internal.set_right(new_node)
        self._nyt.set_parent(new_internal)

        if new_internal != self._root:
            self._update(new_internal.parent)

    def _update(self, node: Node):
        assert isinstance(node, Node)

        block_rep = self._get_block_rep(node.weight)
        if (block_rep != node) and (block_rep != node.parent):
            self._swap(node, block_rep)

        node.increment_weight()
        if node.parent is not None:
            self._update(node.parent)

    def _get_block_rep(self, weight: int) -> Node:
        # get the top-right most node with specific weight
        queue = [self._root]

        while queue:
            node = queue.pop(0)

            if node.weight == weight:
                return node

            if node.left:
                queue.append(node.right)
                queue.append(node.left)

        raise AssertionError

    def _swap(self, n1: Node, n2: Node):
        # swap the entire subtrees
        p1 = n1.parent
        n1_is_left = (p1.left == n1)

        p2 = n2.parent
        n2_is_left = (p2.left == n2)

        n2.set_parent(p1)
        if n1_is_left:
            p1.set_left(n2)
        else:
            p1.set_right(n2)

        n1.set_parent(p2)
        if n2_is_left:
            p2.set_left(n1)
        else:
            p2.set_right(n1)

        tmp = n1.id
        n1.set_id(n2.id)
        n2.set_id(tmp)
