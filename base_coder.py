from typing import Dict
import logging

from huffman_tree import HuffmanTree
from utils import BITS_PER_BYTE


class BaseStaticCoder:
    def __init__(self, verbose: int):
        self._verbose = verbose

        # ===== settings =====
        self._bits_per_symbol: int = 0
        self._bytes_per_symbol: int = 0

        # ===== dummies =====
        self._dummy_symbol_bytes: int = 0   # (total_bytes + dummy_symbol_bytes) % bytes_per_symbol must be 0
        self._dummy_codeword_bits: int = 0  # (bits_of_encoded_content + dummy_codeword_bits) % bits_per_byte must be 0

        # ===== tools =====
        self._tree: HuffmanTree

        self._reset()
        self._logger = logging.getLogger(self.__class__.__name__)

    def _reset(self):
        self._dummy_symbol_bytes = 0
        self._dummy_codeword_bits = 0

    @property
    def settings(self) -> Dict[str, int]:
        return {
            "bytes per symbol": self._bytes_per_symbol,
            "bits per symbol": self._bits_per_symbol,
        }

    @property
    def dummy_info(self) -> Dict[str, int]:
        return {
            "dummy symbol bytes": self._dummy_symbol_bytes,
            "dummy codeword bits": self._dummy_codeword_bits,
        }

    @property
    def bits_per_symbol(self):
        return self._bits_per_symbol

    @property
    def dummy_symbol_bytes(self):
        return self._dummy_symbol_bytes

    @property
    def dummy_symbol_bits(self):
        return self._dummy_codeword_bits


class BaseAdaptiveCoder:
    def __init__(self, period: int):
        assert period > 0

        self._bytes_per_symbol: int = 1
        self._bits_per_symbol: int = self._bytes_per_symbol * BITS_PER_BYTE

        self._period: int = period  # number of symbols between each tree update
        self._total_symbols: int = 0

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
