from typing import Dict, List, Set
import heapq

from adaptive_nodes import Node


class _Block:
    def __init__(self, weight: int):
        self._weight: int = weight
        self._nodes: List[Node] = [] # Min Heap by depth

    @property
    def weight(self):
        return self._weight
    
    @property
    def size(self) -> int:
        return len(self._nodes)

    @property
    def rep(self) -> Node:
        return self._nodes[0]

    def insert(self, node: Node):
        assert node.weight == self._weight
        heapq.heappush(self._nodes, node)

    def remove(self, node: Node):
        self._nodes.remove(node)
        heapq.heapify(self._nodes)

    def update(self):
        heapq.heapify(self._nodes)

class BlockManager:
    def __init__(self):
        self._block_dict: Dict[int, _Block] = {}  # {block.weight: block}
        self._updated_weights: Set[int] = set()  # blocks to be updated

    def insert(self, node: Node):
        w = node.weight

        if w not in self._block_dict:
            self._block_dict[w] = _Block(w)
        
        self._block_dict[w].insert(node)

    def increment_node_weight(self, node: Node):
        self._block_dict[node.weight].remove(node)
        node.increment_weight()
        self.insert(node)

    def get_rep(self, node: Node):
        return self._block_dict[node.weight].rep

    def add_update(self, weight: int):
        # when any node.depth updated
        self._updated_weights.add(weight)

    def update(self):
        for w in self._updated_weights:
            block = self._block_dict[w]

            if block.size == 0:
                self._block_dict.pop(w)
            else:
                self._block_dict[w].update()

        self._updated_weights = set()
