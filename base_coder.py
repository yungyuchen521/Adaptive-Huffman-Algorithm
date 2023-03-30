from typing import Dict
from huffman_tree import HuffmanTree

from utils import BITS_PER_BYTE

class BaseAdaptiveCoder:
    def __init__(self, period: int):
        assert period > 0

        self._bytes_per_symbol: int = 1
        self._bits_per_symbol: int = self._bytes_per_symbol * BITS_PER_BYTE

        self._period: int = period  # number of symbols between each tree update
        self._symbol_cnt: int = 0

        self._symbol_distributions: Dict[str, int] = {
            chr(order): 1
            for order in range(2 ** self._bits_per_symbol)
        }
        self._tree: HuffmanTree
        self._update_cnt = 0
        self._update_tree()
    
    def _update_tree(self):
        self._tree = HuffmanTree(
            symbol_distribution=self._symbol_distributions,
            adaptive=True,
        )
        self._update_cnt += 1
