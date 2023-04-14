from typing import Optional
import sys
from pathlib import Path

from utils import BITS_PER_BYTE, COMP_FILE_EXTENSION
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from adaptive_huffman_tree import AdaptiveHuffmanTree


class AdaptiveEncoder:
    HEADER_SIZE = 3

    def __init__(self, bytes_per_symbol: int):
        self._bytes_per_symbol: int = bytes_per_symbol
        self._bits_per_symbol: int = bytes_per_symbol * BITS_PER_BYTE

        self._symbol_cnt: int = 0
        self._bit_written: int = 0
        
        self._dummy_codeword_bits: int
        self._dummy_symbol_bytes: int = 0
    
    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        if comp_file_path is None:
            comp_file_path = f"{comp_file_path}.{COMP_FILE_EXTENSION}"

        with open(comp_file_path, "wb") as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(chr(0) * self.HEADER_SIZE) # preserve space for header

        self.tree = AdaptiveHuffmanTree(self._bytes_per_symbol)
        with open(src_file_path, "rb") as src, open(comp_file_path, "ab") as comp:
            istream = BitInStream(src, mode=IO_MODE_BYTE)
            ostream = BitOutStream(comp, mode=IO_MODE_BIT)

            while True:
                symbol = istream.read(self._bytes_per_symbol)

                if len(symbol) == 0:
                    break
                elif len(symbol) < self._bytes_per_symbol:
                    self._dummy_symbol_bytes = self._bytes_per_symbol - len(symbol)
                    symbol += chr(0) * self._dummy_symbol_bytes
                
                self._symbol_cnt += 1

                for bit in self.tree.encode(symbol):
                    ostream.write(bit)
                    self._bit_written += 1

            trailing_bits = ostream.flush()
            self._dummy_codeword_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits

        self._write_header(comp_file_path)

    def export_statistics(self, export_path: Path):
        avg_code_len = round(self._bit_written / self._symbol_cnt, 4)

        with open(export_path, "w") as f:
            f.write(f"total symbols: {self._symbol_cnt}\n")
            f.write(f"bits per symbol: {self._bits_per_symbol}\n")
            # f.write(f"entropy: {self.tree.entropy}\n")
            f.write(f"average codeword length: {avg_code_len}\n")

    def _write_header(self, comp_file_path: str):
        assert 0 <= self._dummy_codeword_bits < BITS_PER_BYTE

        with open(comp_file_path, "r+b") as f:
            # {bits per symbol}{dummy codeword bits}{dummy codeword bytes}

            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_codeword_bits))
            stream.write(chr(self._dummy_symbol_bytes))


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])

    export_path = kwargs.get("export", None)
    if export_path:
        export_path = Path(export_path)
        if export_path.exists():
            raise AssertionError("The file already exists!")

    bytes_per_symbol = int(kwargs.get("b", 1))
    src = kwargs["in"]
    comp = kwargs.get("out", f"{src}.{COMP_FILE_EXTENSION}")

    encoder = AdaptiveEncoder(bytes_per_symbol)
    encoder.encode(src, comp)

    if export_path:
        encoder.export_statistics(export_path)
