from typing import Optional, Dict

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    MAX_BYTE_PER_SYMBOL,
    extended_chr,
)
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from huffman_tree import HuffmanTree


class Encoder:
    def __init__(self, bytes_per_symbol: int):
        assert 0 < bytes_per_symbol <= MAX_BYTE_PER_SYMBOL

        self._bytes_per_symbol: int = bytes_per_symbol
        self._bits_per_symbol: int = bytes_per_symbol * BITS_PER_BYTE
        self._symbol_distributions: Dict[str, int] = {}

        self._dummy_symbol_bytes: int = 0
        self._dummy_codeword_bits: int = 0

    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        self._generate_symbol_dist(src_file_path)

        if comp_file_path is None:
            comp_file_path = f"{src_file_path}.comp"

        if len(self._symbol_distributions) == 0:
            with open(comp_file_path, "w"): pass
            return
        elif len(self._symbol_distributions) == 1:
            self._code_dict = { symbol: "0" for symbol in self._symbol_distributions }
        else:
            self._tree = HuffmanTree(symbol_distribution=self._symbol_distributions)
            self._code_dict = self._tree.code_dict

        self._write_header(self._code_dict, comp_file_path)
        self._write_content(self._code_dict, src_file_path, comp_file_path)

    def _generate_symbol_dist(self, src_file_path: str):
        with open(src_file_path, "rb", BUFFER_SIZE) as f:
            stream = BitInStream(f, IO_MODE_BYTE)

            while True:
                symbol = stream.read(self._bytes_per_symbol)
                if len(symbol) == 0:
                    break
                elif len(symbol) < self._bytes_per_symbol:
                    assert self._dummy_symbol_bytes == 0
                    self._dummy_symbol_bytes = self._bytes_per_symbol - len(symbol)
                    symbol += chr(0) * self._dummy_symbol_bytes

                if symbol in self._symbol_distributions:
                    self._symbol_distributions[symbol] += 1
                else:
                    self._symbol_distributions[symbol] = 1

    def _write_header(self, code_dict: Dict[str, str], comp_file_path: str):
        # {bits per symbol}{dummy symbol bytes}{code length table}{dummy codeword bits}

        with open(comp_file_path, "wb", BUFFER_SIZE) as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)

            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_symbol_bytes))

            trailing_bits = 0  # bits insufficient to make a byte
            for order in range(2 ** self._bits_per_symbol):
                symbol = extended_chr(order, self._bits_per_symbol)

                code_len = len(code_dict.get(symbol, ""))
                if code_len > 0:
                    trailing_bits += code_len * self._symbol_distributions[symbol]
                    trailing_bits %= BITS_PER_BYTE

                stream.write(extended_chr(code_len, self._bits_per_symbol))

            self._dummy_codeword_bits = (BITS_PER_BYTE - trailing_bits) % BITS_PER_BYTE
            stream.write(chr(self._dummy_codeword_bits))

    def _write_content(self, code_dict: Dict[str, str], src_file_path: str, comp_file_path: str):
        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(comp_file_path, "ab", BUFFER_SIZE) as comp:
            istream = BitInStream(src, mode=IO_MODE_BYTE)
            ostream = BitOutStream(comp, mode=IO_MODE_BIT)

            while True:
                symbol = istream.read(self._bytes_per_symbol)

                if len(symbol) == 0:
                    break
                elif len(symbol) < self._bytes_per_symbol:
                    assert self._dummy_symbol_bytes == self._bytes_per_symbol - len(symbol)
                    symbol += chr(0) * self._dummy_symbol_bytes

                code_word = code_dict[symbol]
                for c in code_word:
                    ostream.write(c)

            trailing_bits = ostream.flush()
            dummy_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits
            assert self._dummy_codeword_bits == dummy_bits
