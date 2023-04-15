from typing import Dict
import logging

from huffman_tree import HuffmanTree


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
