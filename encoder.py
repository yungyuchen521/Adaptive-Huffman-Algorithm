from typing import Optional, Dict

from bit_io_stream import BitInStream, BitOutStream, IO_MODE_BYTE, IO_MODE_BIT, BITS_PER_BYTE
from huffman_tree import HuffmanTree


class Encoder:
    def __init__(self, bits_per_symbol: int):
        assert 0 < bits_per_symbol < 2**BITS_PER_BYTE and bits_per_symbol % BITS_PER_BYTE == 0

        self._bits_per_symbol: int = bits_per_symbol
        self.BYTES_PER_READ = self._bits_per_symbol // BITS_PER_BYTE
        self._symbol_distributions: Dict[int, int] = {}

        self._dummy_symbol_bytes: int = 0
        self._dummy_codeword_bits: int = 0

    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        self._generate_symbol_dist(src_file_path)

        if comp_file_path is None:
            comp_file_path = f"{src_file_path}.comp"

        if len(self._symbol_distributions) == 0:
            with open(comp_file_path, "w"):
                pass
            return
        elif len(self._symbol_distributions) == 1:
            self._code_dict = { order: "0" for order, _ in self._symbol_distributions.items() }
        else:
            self._tree = HuffmanTree(symbol_distribution=self._symbol_distributions)
            self._code_dict = self._tree.code_dict

        self._write_header(self._code_dict, comp_file_path)
        self._write_content(self._code_dict, src_file_path, comp_file_path)

    def _generate_symbol_dist(self, src_file_path: str):
        with open(src_file_path, "rb") as f:
            stream = BitInStream(f, IO_MODE_BYTE)

            while True:
                symbol_order = stream.read()
                if symbol_order == BitInStream.EOF:
                    break
                # elif len(symbol) < self.BYTES_PER_READ:
                #     self._dummy_symbol_bytes = self.BYTES_PER_READ - len(symbol)
                #     symbol += chr(0) * self._dummy_symbol_bytes

                if symbol_order in self._symbol_distributions:
                    self._symbol_distributions[symbol_order] += 1
                else:
                    self._symbol_distributions[symbol_order] = 1

    def _write_header(self, code_dict: Dict[int, str], comp_file_path: str):
        # {bits per symbol}{dummy symbol bytes}{code length table}{dummy codeword bits}

        with open(comp_file_path, "wb") as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)

            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_symbol_bytes))

            trailing_bits = 0  # bits insufficient to make a byte
            for order in range(2 ** self._bits_per_symbol):
                code_len = len(code_dict.get(order, ""))
                if code_len > 0:
                    trailing_bits += code_len * self._symbol_distributions[order]
                    trailing_bits %= BITS_PER_BYTE

                stream.write(chr(code_len))

            self._dummy_codeword_bits = (BITS_PER_BYTE - trailing_bits) % BITS_PER_BYTE
            stream.write(chr(self._dummy_codeword_bits))

    def _write_content(self, code_dict: Dict[int, str], src_file_path: str, comp_file_path: str):
        with open(src_file_path, "rb") as src, open(comp_file_path, "ab") as comp:
            istream = BitInStream(src, mode=IO_MODE_BYTE)
            ostream = BitOutStream(comp, mode=IO_MODE_BIT)

            while True:
                symbol_order = istream.read()

                if symbol_order == BitInStream.EOF:
                    break
                # elif len(symbol) < self.BYTES_PER_READ:
                #     assert self._dummy_symbol_bytes == self.BYTES_PER_READ - len(symbol)
                #     symbol += chr(0) * self._dummy_symbol_bytes

                code_word = code_dict[symbol_order]
                for c in code_word:
                    ostream.write(c)

            trailing_bits = ostream.flush()
            dummy_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits
            assert self._dummy_codeword_bits == dummy_bits
