from typing import Dict, List, Optional

from utils import BITS_PER_BYTE, BYTES_PER_MB, extended_chr, extended_ord
from adaptive_nodes import BaseNode, Node, NYT
from block import BlockManager


ENCODE_MODE = "ENCODE"
DECODE_MODE = "DECODE"

class AdaptiveHuffmanTree:
    def __init__(self, bytes_per_symbol: int, mode: str, shrink_period: int = 0, shrink_factor: int = 2):
        self._bytes_per_symbol: int = bytes_per_symbol
        self._bits_per_symbol: int = bytes_per_symbol * BITS_PER_BYTE

        assert mode in (ENCODE_MODE, DECODE_MODE)
        self._mode = mode

        self._shrink_period: int = shrink_period * BYTES_PER_MB
        self._shrink_cnt: int = 0
        self._shrink_factor: int = shrink_factor

        self._symbol_cnt: int = 0

        self._nyt: NYT = NYT(self._bits_per_symbol)
        self._root: BaseNode = self._nyt

        self._block_manager: BlockManager = BlockManager()

        self._node_id: int = 0  # assign unique id to each node (for debug purpose)

        # for encoder
        self._ord_node_dict: Dict[int, Node]  = {}

        # for decoder
        self._cur: BaseNode = self._root
    
    @property
    def symbol_cnt(self):
        return self._symbol_cnt

    # @property  # inaccurate if shrunk
    # def entropy(self) -> float:
    #     ent = 0
    #     stack = [self._root]

    #     while stack:
    #         node = stack[-1]
    #         if isinstance(node, Node) and node.is_symbol:
    #             p = node.weight / self._symbol_cnt
    #             ent -= p * log2(p)

    #         if node.left:
    #             stack.append(node.left)
    #             stack.append(node.right)

    #     return ent

    @property
    def shrink_cnt(self) -> int:
        return self._shrink_cnt

    def __str__(self):
        # (depth, Node)
        queue: List[BaseNode] = [self._root]
        
        s = ""
        depth = 0
        while queue:
            n = queue.pop(0)

            if n.depth > depth:
                assert n.depth == depth+1
                s += "\n"
                depth = n.depth
            
            s += f"[{str(n)}] "

            if n.left:
                queue.append(n.left)
                queue.append(n.right)

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

        self._block_manager.update()

        if self._should_shrink():
            self._shrink()
    
        return code

    def decode(self, bit: str) -> Optional[str]:
        # whenever a non-null symbol returned
        # self._cur should be set to self._root

        assert bit == "0" or bit == "1"

        if isinstance(self._cur, NYT):
            symbol = self._nyt.decode(bit)

            if symbol is not None:
                self._symbol_cnt += 1
                self._create_new_node(extended_ord(symbol))
                # tree updated in create_new_node

                self._cur = self._root
                self._block_manager.update()

                if self._should_shrink():
                    self._shrink()

            return symbol

        self._cur = (
            self._cur.left
            if bit == "0"
            else self._cur.right
        )

        if isinstance(self._cur, Node) and self._cur.is_symbol:
            self._symbol_cnt += 1
            symbol = extended_chr(self._cur.order, self._bits_per_symbol)

            self._update(self._cur)
            self._cur = self._root
            self._block_manager.update()

            if self._should_shrink():
                self._shrink()

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

            if isinstance(node, Node):
                assert node.parent.depth + 1 == node.depth

            node = node.parent

        return code

    def _create_new_node(self, order: int):
        new_internal = Node(
            id=self._get_next_node_id(),
            parent=self._nyt.parent,
            weight=1,
        )
        if new_internal.parent is None:
            self._root = new_internal
        else:
            new_internal.parent.set_left(new_internal)

        new_node = Node(
            id=self._get_next_node_id(),
            parent=new_internal,
            weight=1,
            order=order,
        )
        if self._mode == ENCODE_MODE:
            self._ord_node_dict[order] = new_node

        new_internal.set_left(self._nyt)
        new_internal.set_right(new_node)
        self._nyt.set_parent(new_internal)

        self._block_manager.insert(new_internal)
        self._block_manager.insert(new_node)

        if new_internal != self._root:
            self._update(new_internal.parent)

    def _get_next_node_id(self) -> int:
        self._node_id += 1
        return self._node_id

    def _update(self, node: Node):
        assert isinstance(node, Node)

        block_rep = self._block_manager.get_rep(node)
        if (block_rep != node) and (block_rep != node.parent):
            self._swap(node, block_rep)

        self._block_manager.increment_node_weight(node)

        if node.parent is not None:
            self._update(node.parent)

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

        self._update_depth(n1)
        self._update_depth(n2)

    def _update_depth(self, node: Node):
        if not isinstance(node, Node):
            return

        node.update_depth()
        self._block_manager.add_update(node.weight)

        if node.left:
            self._update_depth(node.left)
            self._update_depth(node.right)

    def _should_shrink(self) -> bool:
        return (
            self._shrink_period > 0 and isinstance(self._root, Node) and
            self._symbol_cnt * self._bytes_per_symbol > self._shrink_period * (self._shrink_cnt+1)
        )

    def _shrink(self):
        def shrink(node: Node):
            if isinstance(node.left, Node):
                shrink(node.left)
            if isinstance(node.right, Node):
                shrink(node.right)

            if node.is_symbol:
                node.shrink(self._shrink_factor)
            else:
                node.update_weight()

        assert self._should_shrink()        
        self._shrink_cnt += 1
        shrink(self._root)
        self._block_manager.shrink()
