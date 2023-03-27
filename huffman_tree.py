from typing import Dict, List, Optional
import heapq


class BaseNode:
    def __init__(self, order: int, left=None, right=None):
        # if order < 0:
        #     assert isinstance(left, BaseNode)
        #     assert isinstance(right, BaseNode)
        # else:
        #     assert left is None
        #     assert right is None

        self._order: int = order
        self._left: BaseNode = left
        self._right: BaseNode = right

    def __lt__(self, node):
        raise NotImplementedError

    @property
    def is_symbol(self):
        return self._order >= 0

    @property
    def order(self):
        return self._order

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right
    
    @property
    def freq(self):
        raise NotImplementedError()
    
    @property
    def code_len(self):
        raise NotImplementedError()


class FreqNode(BaseNode):
    def __init__(self, freq: int, order: int=-1, left: Optional[BaseNode]=None, right: Optional[BaseNode]=None):
        super().__init__(order, left, right)
        self._freq: int = freq

    def __str__(self):
        return f"freq={self._freq}||order={self._order}"

    def __lt__(self, node):
        return (
            self._order < node.order
            if self._freq == node.freq
            else self._freq < node.freq 
        )

    @property
    def freq(self):
        return self._freq


class CodeLenNode(BaseNode):
    def __init__(self, code_len: Optional[int]=None, order: int=-1):
        super().__init__(order, None, None)
        
        self._code_len = code_len
        self._order = order

    def __str__(self):
        return f"code_len={self._code_len}||chr={chr(self._order) if self._order >= 0 else None}"

    def __lt__(self, node):
        assert self._order is not None and node.order is not None
        assert self._order >= 0 and node.order >= 0
        return (
            self._order > node.order
            if self._code_len == node.code_len 
            else self._code_len > node.code_len 
        )

    @property
    def code_len(self):
        return self._code_len
    
    def set_left(self, node):
        assert isinstance(node, CodeLenNode)
        assert self._left is None
        self._left = node

    def set_right(self, node):
        assert isinstance(node, CodeLenNode)
        assert self._right is None
        self._right = node


class HuffmanTree:
    def __init__(self, symbol_distribution: Dict[int, int]=None, code_len_table: List[int]=None):
        self._root: BaseNode
        self._code_dict: Dict[int, str] = {}  # for encoding only
        self._code_len_dict: Dict[int, int] = {}
        self._cur: BaseNode  # for decoding only

        if symbol_distribution:
            self._build_by_distribution(symbol_distribution)
            self._set_code_len_dict(self._root, 0)
            self._build_by_code_len()
            self._set_code_dict(self._root, "")

            # ==================== for debug purpose only ==================== 
            for order, code in self._code_dict.items():
                if len(code) != self._code_len_dict[order]:
                    print(f"{chr(order)}: original code len = {self._code_len_dict[order]}, after rebuilt is {len(code)} ({code})")
        elif code_len_table:
            self._code_len_dict = {
                order: code_len
                for order, code_len in enumerate(code_len_table)
                if code_len > 0
            }
            self._build_by_code_len()
            self._set_code_dict(self._root, "")  # for debug purpose only
        else:
            raise AssertionError("Either symbol distribution or code length table must be given.")

    @property
    def code_dict(self):
        return self._code_dict

    def decode(self, bits: str):
        for b in bits:
            assert b in "01"

            self._cur = (
                self._cur.left
                if b == "0"
                else self._cur.right
            )

            if self._cur.is_symbol:
                yield self._cur.order
                self._cur = self._root

    def _build_by_distribution(self, symbol_distribution: Dict[int, int]):
        nodes = [
            FreqNode(freq=count, order=order) 
            for order, count in symbol_distribution.items()
        ]

        heapq.heapify(nodes)
        while len(nodes) > 1:
            n1 = heapq.heappop(nodes)
            n2 = heapq.heappop(nodes)

            parent = FreqNode(
                freq=n1.freq+n2.freq,
                left=n1,
                right=n2,
            )

            heapq.heappush(nodes, parent)

        self._root = nodes.pop()

    def _build_by_code_len(self):
        symbol_nodes = [
            CodeLenNode(code_len=code_len, order=order)
            for order, code_len in self._code_len_dict.items()
        ]
        symbol_nodes.sort() # sort in descending order by code_len
        max_code_len = symbol_nodes[0].code_len

        self._root = CodeLenNode()
        self._cur = self._root
        parents = [self._root]

        for code_len in range(1, max_code_len+1):
            if code_len != symbol_nodes[-1].code_len:
                new_nodes = []
            else:
                index = self._binary_search_node(symbol_nodes, code_len)
                assert index != -1

                new_nodes = symbol_nodes[index:]
                symbol_nodes = symbol_nodes[:index]

            new_parents = []
            for p in parents:
                if new_nodes:
                    p.set_left(new_nodes.pop())
                else:
                    n = CodeLenNode()
                    p.set_left(n)
                    new_parents.append(n)

                if new_nodes:
                    p.set_right(new_nodes.pop())
                else:
                    n = CodeLenNode()
                    p.set_right(n)
                    new_parents.append(n)
            
            parents = new_parents
            code_len += 1

        assert len(symbol_nodes) == 0

    def _set_code_len_dict(self, node: BaseNode, l: int):
        if node.is_symbol:
            self._code_len_dict[node.order] = l
        else:
            self._set_code_len_dict(node.left, l+1)
            self._set_code_len_dict(node.right, l+1)

    def _set_code_dict(self, node: BaseNode, code: str):
        if node.is_symbol:
            self._code_dict[node.order] = code
        else:
            self._set_code_dict(node.left, f"{code}0")
            self._set_code_dict(node.right, f"{code}1")

    @staticmethod
    def _binary_search_node(nodes: List[CodeLenNode], target: int) -> int:
        # nodes are sorted in descending order by code_len
        left, right = 0, len(nodes) - 1

        index = right+1
        while left <= right:
            mid = (left + right) // 2
            l = nodes[mid].code_len
            assert l is not None

            if l > target:
                left = mid+1
            elif l <= target:
                if l == target:
                    index = min(mid, index)

                right = mid-1

        return (-1 if index >= len(nodes) else index)
