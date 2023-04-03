from typing import Dict, Optional
from math import ceil, log2
from pathlib import Path
import os
import sys

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    MAX_BYTE_PER_SYMBOL,
    COMP_FILE_EXTENSION,
    extended_chr,
    extended_ord,
)
from base_coder import BaseStaticCoder
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from huffman_tree import HuffmanTree


class Encoder(BaseStaticCoder):
    def __init__(self, bytes_per_symbol: int, verbose: int=0):
        assert 0 < bytes_per_symbol <= MAX_BYTE_PER_SYMBOL
        super().__init__(verbose)

        self._bytes_per_symbol = bytes_per_symbol
        self._bits_per_symbol = bytes_per_symbol * BITS_PER_BYTE

        self._src_file_path: str
        self._comp_file_path: str

        self._total_symbols: int = 0                     # number of symbols in the original file
        self._symbol_distributions: Dict[str, int] = {}  # count for each symbol in the file
        self._bits_written: int

    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        self._reset()
        self._generate_symbol_dist(src_file_path)

        if comp_file_path is None:
            comp_file_path = f"{src_file_path}.{COMP_FILE_EXTENSION}"

        self._src_file_path = src_file_path
        self._comp_file_path = comp_file_path

        if len(self._symbol_distributions) < 2:
            raise NotImplementedError()
        else:
            self._tree = HuffmanTree(symbol_distribution=self._symbol_distributions)

        self._write_header(comp_file_path)
        self._write_content(src_file_path, comp_file_path)

        if self._verbose > 0:
            comp_ratio = self.get_compression_ratio(False)
            self._logger.warning(f"compression ratio: {comp_ratio}")

    def get_compression_ratio(self, consider_header: bool=True) -> float:
        comp_size = ceil(self._bits_written / BITS_PER_BYTE)
        if consider_header:
            header_size = 0
            header_size += 2 # bits per symbol, dummy symbol bytes
            header_size += self._bytes_per_symbol # size of codelen_dict
            header_size += len(self.code_dict) * 2 * self._bytes_per_symbol # code length dict
            header_size += 1 # dummy codeword bits
            comp_size += header_size

        return 1 - comp_size / self.total_bytes

    def export_statistics(self, dir_path: Path):
        with open(dir_path/"stats.txt", "w") as f:
            f.write(f"bytes per symbol: {self._bytes_per_symbol}\n")
            f.write(f"total symbols: {self._total_symbols}\n")

        with open(dir_path/"distributions.txt", "w") as f:
            for symbol, cnt in self._symbol_distributions.items():
                f.write(f"{extended_ord(symbol)}: {cnt}\n")

        with open(dir_path/"code.txt", "w") as f:
            for symbol, code in self.code_dict.items():
                f.write(f"{extended_ord(symbol)}: {code}\n")

        with open(dir_path/"performance.txt", "w") as f:
            f.write(f"entropy: {self.entropy}\n")
            f.write(f"average codeword length: {self.code_len_per_symbol}\n")
            f.write(f"compression ratio (including header): {self.get_compression_ratio(consider_header=True)}\n")
            f.write(f"compression ratio (without header): {self.get_compression_ratio(consider_header=False)}\n")

    @property
    def total_symbols(self):
        return self._total_symbols

    @property
    def total_bytes(self) -> int:
        return self._total_symbols * self._bytes_per_symbol - self._dummy_symbol_bytes

    @property
    def symbol_distributions(self):
        return self._symbol_distributions

    @property
    def entropy(self) -> float:
        ent = 0

        for cnt in self._symbol_distributions.values():
            p = cnt / self._total_symbols
            ent -= p * log2(p)
        
        return ent

    @property
    def code_dict(self) -> Dict[str, str]:
        return self._tree.code_dict

    @property
    def code_len_per_symbol(self) -> float:
        total_codelen = 0

        for symbol, cnt in self._symbol_distributions.items():
            total_codelen += cnt * len(self.code_dict[symbol])
        
        return total_codelen / self._total_symbols

    @property
    def code_len_per_byte(self) -> float:
        return self.code_len_per_symbol / self._bytes_per_symbol

    def _reset(self):
        super()._reset()
        self._total_symbols = 0
        self._symbol_distributions = {}
        self._bits_written = 0

    def _generate_symbol_dist(self, src_file_path: str):
        if self._verbose > 0:
            self._logger.warning(f"{self.__class__.__name__} calculating symbol distribution...")

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
                
                self._total_symbols += 1

    def _write_header(self, comp_file_path: str):
        if self._verbose > 0:
            self._logger.warning(f"{self.__class__.__name__} writing compression header...")

        # {bits per symbol}{dummy symbol bytes}{size of codelen_dict}{code length dict}{dummy codeword bits}
        # {code length dict} = {symbol}{code length}{symbol}{code length}{symbol}{code length}...
        code_dict = self._tree.code_dict

        with open(comp_file_path, "wb", BUFFER_SIZE) as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)

            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_symbol_bytes))

            if len(code_dict) == 2 ** self._bits_per_symbol:
                # 0 is never used, used it to represent 2 ** self._bits_per_symbol
                stream.write(extended_chr(0, self._bits_per_symbol))
            else:
                stream.write(extended_chr(len(code_dict), self._bits_per_symbol))

            trailing_bits = 0  # bits insufficient to make a byte
            for symbol, code in code_dict.items():
                code_len = len(code)
                
                trailing_bits += code_len * self._symbol_distributions[symbol]
                trailing_bits %= BITS_PER_BYTE

                stream.write(symbol)

                if code_len == 2 ** self._bits_per_symbol:
                    # 0 is never used, used it to represent 2 ** self._bits_per_symbol
                    stream.write(extended_chr(0, self._bits_per_symbol))
                else:
                    stream.write(extended_chr(code_len, self._bits_per_symbol))

            self._dummy_codeword_bits = (BITS_PER_BYTE - trailing_bits) % BITS_PER_BYTE
            stream.write(chr(self._dummy_codeword_bits))

    def _write_content(self, src_file_path: str, comp_file_path: str):
        if self._verbose > 0:
            self._logger.warning(f"{self.__class__.__name__} compressing file content")

        code_dict = self._tree.code_dict

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

                for bit in code_dict[symbol]:
                    self._bits_written += 1
                    ostream.write(bit)

            trailing_bits = ostream.flush()
            dummy_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits
            assert self._dummy_codeword_bits == dummy_bits


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])

    export_path = kwargs.get("export", None)
    if export_path:
        export_path = Path(export_path)
        if export_path.exists():
            raise AssertionError("The folder already exists. Files insider may be overwritten!")
        else:
            os.mkdir(export_path)

    bytes_per_symbol = int(kwargs.get("b", 1))
    verbose = int(kwargs.get("v", 0))
    src = kwargs["in"]
    comp = kwargs.get("out", f"{src}.{COMP_FILE_EXTENSION}")

    encoder = Encoder(bytes_per_symbol=bytes_per_symbol, verbose=verbose)
    encoder.encode(src, comp)

    if export_path:
        encoder.export_statistics(export_path)
