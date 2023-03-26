from typing import Optional
from io import TextIOWrapper

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
)
from huffman_tree import HuffmanTree


class Decoder:
    def __init__(self):
        self._bits_per_symbol: int
        self.BYTES_PER_READ: int
        self._dummy_symbol_bytes: int
        self._dummy_codeword_bits: int
        self._tree: HuffmanTree

    def decode(self, src_file_path, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.decomp"

        with open(src_file_path, "r", BUFFER_SIZE) as src, open(decomp_file_path, "w", BUFFER_SIZE) as decomp:
            self._parse_header(src)

            bits = src.read()
            for order in self._tree.decode(bits):
                symbol = chr(order)
                decomp.write(symbol)

    def _parse_header(self, file_obj: TextIOWrapper):
        self._bits_per_symbol = ord(file_obj.read(1))
        self.BYTES_PER_READ = self._bits_per_symbol // BITS_PER_BYTE
        
        self._dummy_symbol_bytes = ord(file_obj.read(1))

        code_len_table = [
            ord(file_obj.read(1)) 
            for _ in range(2 ** self._bits_per_symbol)
        ]

        self._dummy_codeword_bits = ord(file_obj.read(1))

        self._tree = HuffmanTree(code_len_table=code_len_table)
        self._code_dict = self._tree.code_dict  # for debug purpose
