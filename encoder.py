from typing import Dict
from math import log2
from pathlib import Path
import sys

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    COMP_FILE_EXTENSION,
    extended_chr,
)
from base_coder import BaseEncoder
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from huffman_tree import HuffmanTree


class Encoder(BaseEncoder):
    PROGRESS_CALULATE_SYMBOLS = "CALCULATE_SYMBOLS"
    PROGRESS_WRITE_HEADER = "WRITE_HEADER"
    PROGRESS_WRITE_CONTENT = "WRITE_CONTENT"

    def __init__(self, bytes_per_symbol: int, verbose: int=0):
        super().__init__(bytes_per_symbol, verbose)

        self._current_progress = None
        self._symbol_distributions: Dict[str, int] = {}  # count for each symbol in the file

    def encode(self, src_file_path: str, comp_file_path: str):
        self._calculate_symbol_dist(src_file_path)

        if len(self._symbol_distributions) < 2:
            raise NotImplementedError()
        else:
            self._tree = HuffmanTree(symbol_distribution=self._symbol_distributions)

        self._write_header(comp_file_path)
        self._write_content(src_file_path, comp_file_path)

    def export_results(self, export_path: Path):
        with open(export_path, "w") as f:
            f.write(f"{'='*10} params {'='*10}\n")
            f.write(f"bytes per symbol: {self._bytes_per_symbol}\n")

            f.write(f"\n{'='*10} statistics {'='*10}\n")
            f.write(f"total symbols: {self._symbol_cnt}\n")
            f.write(f"header size: {self._get_header_size()}\n")
            f.write(f"entropy: {self.entropy}\n")
            f.write(f"average codeword length: {self.avg_codeword_len}\n")
            f.write(f"compression ratio: {self.compression_ratio}\n")

    @property
    def symbol_distributions(self):
        assert self._current_progress not in [None, self.PROGRESS_CALULATE_SYMBOLS]
        return self._symbol_distributions

    @property
    def entropy(self) -> float:
        assert self._current_progress not in [None, self.PROGRESS_CALULATE_SYMBOLS]
        
        ent = 0
        for cnt in self._symbol_distributions.values():
            p = cnt / self._symbol_cnt
            ent -= p * log2(p)

        return ent

    @property
    def code_dict(self) -> Dict[str, str]:
        assert self._current_progress not in [None, self.PROGRESS_CALULATE_SYMBOLS]
        return self._tree.code_dict

    @property
    def avg_codeword_len(self) -> float:
        assert self._current_progress not in [None, self.PROGRESS_CALULATE_SYMBOLS]

        total_codelen = 0
        for symbol, cnt in self._symbol_distributions.items():
            total_codelen += cnt * len(self.code_dict[symbol])

        return total_codelen / self._symbol_cnt

    def _calculate_symbol_dist(self, src_file_path: str):
        self._current_progress = self.PROGRESS_CALULATE_SYMBOLS
        self._dummy_symbol_bytes = 0

        with open(src_file_path, "rb", BUFFER_SIZE) as f:
            stream = BitInStream(f, IO_MODE_BYTE)

            while True:
                symbol = stream.read(self._bytes_per_symbol)
                if len(symbol) == 0:
                    break
                elif len(symbol) < self._bytes_per_symbol:
                    self._dummy_symbol_bytes = self._bytes_per_symbol - len(symbol)
                    symbol += chr(0) * self._dummy_symbol_bytes

                if symbol in self._symbol_distributions:
                    self._symbol_distributions[symbol] += 1
                else:
                    self._symbol_distributions[symbol] = 1

    def _write_header(self, comp_file_path: str):
        """
            bits per symbol: 1 byte
            dummy symbol bytes: 1 byte
            size of codelen_dict: `bytes_per_symbol` bytes
            code length dict: {symbol}{code length}{symbol}{code length}{symbol}{code length}...
                symbol: `bytes_per_symbol` bytes
                code length: `bytes_per_symbol` bytes
            dummy codeword bits: 1 byte
        """

        self._current_progress = self.PROGRESS_WRITE_HEADER

        with open(comp_file_path, "wb", BUFFER_SIZE) as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)

            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_symbol_bytes))

            if len(self.code_dict) == 2 ** self._bits_per_symbol:
                # 0 is never used, use it to represent 2 ** self._bits_per_symbol
                stream.write(extended_chr(0, self._bits_per_symbol))
            else:
                stream.write(extended_chr(len(self.code_dict), self._bits_per_symbol))

            trailing_bits = 0  # bits insufficient to make a byte
            for symbol, code in self.code_dict.items():
                code_len = len(code)
                
                trailing_bits += code_len * self._symbol_distributions[symbol]
                trailing_bits %= BITS_PER_BYTE

                stream.write(symbol)

                if code_len == 2 ** self._bits_per_symbol:
                    # 0 is never used, use it to represent 2 ** self._bits_per_symbol
                    stream.write(extended_chr(0, self._bits_per_symbol))
                else:
                    stream.write(extended_chr(code_len, self._bits_per_symbol))

            self._dummy_codeword_bits = (BITS_PER_BYTE - trailing_bits) % BITS_PER_BYTE
            stream.write(chr(self._dummy_codeword_bits))

    def _write_content(self, src_file_path: str, comp_file_path: str):
        self._current_progress = self.PROGRESS_WRITE_CONTENT

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

                self._symbol_cnt += 1
                for bit in self.code_dict[symbol]:
                    self._bits_written += 1
                    ostream.write(bit)

            trailing_bits = ostream.flush()
            dummy_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits
            assert self._dummy_codeword_bits == dummy_bits

    def _get_header_size(self) -> int:
        header_size = 2  # bits per symbol, dummy symbol bytes
        header_size += self._bytes_per_symbol  # size of codelen_dict
        header_size += len(self.code_dict) * 2 * self._bytes_per_symbol # code length dict
        header_size += 1  # dummy codeword bits
        return header_size


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])

    export_path = kwargs.get("export", None)
    if export_path:
        export_path = Path(export_path)
        if export_path.exists():
            raise AssertionError(f"{export_path} already exists")

    bytes_per_symbol = int(kwargs.get("b", 1))
    verbose = int(kwargs.get("v", 0))

    src = kwargs["in"]
    comp = kwargs.get("out", f"{src}.{COMP_FILE_EXTENSION}")

    encoder = Encoder(bytes_per_symbol=bytes_per_symbol, verbose=verbose)
    encoder.encode(src, comp)

    if export_path:
        encoder.export_results(export_path)
