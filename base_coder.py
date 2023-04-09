from typing import Dict
import logging

from huffman_tree import HuffmanTree
from utils import extended_chr


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


class BasePeriodicCoder:
    def __init__(self, p: int):
        assert 10 <= p <= 20
        self._p: int = p

        # number of symbols between each tree update
        # range[2^10, 2^20] = range[1K symbols, 1M symbols]
        self._period: int = 2 ** p

        self._total_symbols: int = 0
        self._bits_written: int = 0

        self._bytes_per_symbol: int
        self._bits_per_symbol: int

        self._symbol_distributions: Dict[str, int] = {
            extended_chr(order, self._bits_per_symbol): 1
            for order in range(2 ** self._bits_per_symbol)
        }
        self._tree: HuffmanTree
        self._update_cnt = 0
        self._update_tree()

    @property
    def code_len_per_symbol(self) -> float:
        return self._bits_written / self._total_symbols

    @property
    def code_len_per_byte(self) -> float:
        return self.code_len_per_symbol / self._bytes_per_symbol

    def _update_tree(self):
        self._tree = HuffmanTree(
            symbol_distribution=self._symbol_distributions,
            adaptive=True,
        )
        self._update_cnt += 1
