from typing import Optional, BinaryIO
import io
import sys

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    DECOMP_FILE_EXTENSION,
)
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from base_coder import BaseAdaptiveCoder


class AdaptiveDecoder(BaseAdaptiveCoder):
    BITS_PER_READ = 256  # more convenient to strip off dummy bits & dummy bytes

    def __init__(self):
        self._dummy_codeword_bits: int
        self._dummy_symbol_bytes: int

    def decode(self, src_file_path: str, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.{DECOMP_FILE_EXTENSION}"

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(decomp_file_path, "wb", BUFFER_SIZE) as decomp:
            self._parse_header(src)
            super().__init__(self._p)
            
            istream = BitInStream(src, mode=IO_MODE_BIT)
            ostream = BitOutStream(decomp, mode=IO_MODE_BYTE)

            next_bit_seq = istream.read(self.BITS_PER_READ)
            while next_bit_seq:
                curr_bit_seq = next_bit_seq
                next_bit_seq = istream.read(self.BITS_PER_READ)

                if not next_bit_seq and self._dummy_codeword_bits > 0:
                    curr_bit_seq = curr_bit_seq[:-self._dummy_codeword_bits]

                for bit in curr_bit_seq:
                    symbol = self._tree.decode(bit)
                    if symbol:
                        ostream.write(symbol)
                        self._total_symbols += 1
                        self._symbol_distributions[symbol] += 1

                        if self._total_symbols % self._period == 0:
                            self._update_tree()
        
        self._trunc(decomp_file_path)

    def  _parse_header(self, file_obj: BinaryIO):
        # {p}{bits per symbol}{dummy symbol bytes}{dummy codeword bits}
        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)

        self._p = ord(stream.read(1))
        self._bits_per_symbol = ord(stream.read(1))
        self._bytes_per_symbol = self._bits_per_symbol // BITS_PER_BYTE
        self._dummy_symbol_bytes = ord(stream.read(1))
        self._dummy_codeword_bits = ord(stream.read(1))

    def _trunc(self, decomp_file_path: str):
        # strip off dummy symbol bytes
        if self._dummy_symbol_bytes == 0:
            return

        with open(decomp_file_path, "r+b") as f:
            f.seek(-self._dummy_symbol_bytes, io.SEEK_END)
            f.truncate()


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])
    
    decoder = AdaptiveDecoder()
    src = kwargs["in"]
    decomp = kwargs.get("out", f"{src}.{DECOMP_FILE_EXTENSION}")

    decoder.decode(src, decomp)
