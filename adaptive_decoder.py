from typing import BinaryIO, Optional
import sys

from utils import DECOMP_FILE_EXTENSION, BITS_PER_BYTE
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BIT,
    IO_MODE_BYTE,
)
from adaptive_huffman_tree import AdaptiveHuffmanTree


class AdaptiveDecoder:
    BITS_PER_READ = 256  # more convenient to strip off dummy bits & dummy bytes

    def __init__(self):
        self._bits_per_symbol: int
        self._bytes_per_symbol: int
        self._dummy_codeword_bits: int

    def decode(self, src_file_path: str, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.{DECOMP_FILE_EXTENSION}"
        
        with open(src_file_path, "rb") as src, open(decomp_file_path, "wb") as decomp:
            self._parse_header(src)
            tree = AdaptiveHuffmanTree(self._bytes_per_symbol)

            istream = BitInStream(src, mode=IO_MODE_BIT)
            ostream = BitOutStream(decomp, mode=IO_MODE_BYTE)

            next_bit_seq = istream.read(self.BITS_PER_READ)
            while next_bit_seq:
                curr_bit_seq = next_bit_seq
                next_bit_seq = istream.read(self.BITS_PER_READ)

                if not next_bit_seq and self._dummy_codeword_bits > 0:
                    curr_bit_seq = curr_bit_seq[:-self._dummy_codeword_bits]

                for bit in curr_bit_seq:
                    symbol = tree.decode(bit)
                    if symbol:
                        ostream.write(symbol)

    def _parse_header(self, file_obj: BinaryIO):
        # {bits per symbol}{dummy codeword bits}

        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)
        self._bits_per_symbol = ord(stream.read(1))
        self._dummy_codeword_bits = ord(stream.read(1))

        print(self._bits_per_symbol)
        assert self._bits_per_symbol > 0 and self._bits_per_symbol % 8 == 0
        self._bytes_per_symbol = self._bits_per_symbol // BITS_PER_BYTE


if __name__ == "__main__" or True:
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])
    
    decoder = AdaptiveDecoder()
    src = kwargs["in"]
    decomp = kwargs.get("out", f"{src}.{DECOMP_FILE_EXTENSION}")

    decomp = None
    decoder.decode(src, decomp)
