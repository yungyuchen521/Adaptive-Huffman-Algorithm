from typing import Optional
from pathlib import Path
import os
import sys

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    COMP_FILE_EXTENSION,
)
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from base_coder import BasePeriodicCoder


class AdaptiveEncoder(BasePeriodicCoder):
    def __init__(self, p: int, bytes_per_symbol: int):
        self._p = p
        self._bytes_per_symbol = bytes_per_symbol
        self._bits_per_symbol = bytes_per_symbol * BITS_PER_BYTE
        super().__init__(p)

        self._dummy_symbol_bytes: int = 0
        self._dummy_codeword_bits: int = 0

    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        if comp_file_path is None:
            comp_file_path = f"{src_file_path}.{COMP_FILE_EXTENSION}"

        with open(comp_file_path, "w") as f:
            f.write(chr(0) * 4) # preserve spaces for header

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(comp_file_path, "ab", BUFFER_SIZE) as comp:
            istream = BitInStream(src, mode=IO_MODE_BYTE)
            ostream = BitOutStream(comp, mode=IO_MODE_BIT)

            while True:
                symbol = istream.read(self._bytes_per_symbol)

                if len(symbol) == 0:
                    break
                elif len(symbol) < self._bytes_per_symbol:
                    self._dummy_symbol_bytes = self._bytes_per_symbol - len(symbol)
                    symbol += chr(0) * self._dummy_symbol_bytes

                self._total_symbols += 1
                self._symbol_distributions[symbol] += 1

                for bit in self._tree.code_dict[symbol]:
                    ostream.write(bit)
                    self._bits_written += 1
                
                if self._total_symbols % self._period == 0:
                    self._update_tree()

            trailing_bits = ostream.flush()
            assert 0 <= trailing_bits < BITS_PER_BYTE 
            self._dummy_codeword_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits

        self._write_header(comp_file_path)

    @property
    def compression_ratio(self) -> float:
        org_size = self._total_symbols * self._bytes_per_symbol
        comp_size = self._bits_written / BITS_PER_BYTE
        return 1 - (comp_size / org_size)

    def export_statistics(self, dir_path: Path):
        with open(dir_path/"stats.txt", "w") as f:
            f.write(f"bytes per symbol: {self._bytes_per_symbol}\n")
            f.write(f"update period: {self._period} (million symbols)\n")
            f.write(f"total symbols: {self._total_symbols}\n")
            f.write(f"update count: {self._update_cnt}\n")
            f.write(f"code length per symbol: {self.code_len_per_symbol}\n")
            f.write(f"code length per byte: {self.code_len_per_byte}\n")
            f.write(f"compression ratio: {self.compression_ratio}\n")

    def _write_header(self, comp_file_path: str):
        # {p}{bits per symbol}{dummy symbol bytes}{dummy codeword bits}
        
        with open(comp_file_path, "r+b", BUFFER_SIZE) as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(chr(self._p))
            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_symbol_bytes))
            stream.write(chr(self._dummy_codeword_bits))

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
    p = int(kwargs.get("p", 10))
    src = kwargs["in"]
    comp = kwargs.get("out", f"{src}.{COMP_FILE_EXTENSION}")

    encoder = AdaptiveEncoder(p=p, bytes_per_symbol=bytes_per_symbol)
    encoder.encode(src, comp)

    if export_path:
        encoder.export_statistics(export_path)
