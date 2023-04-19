from typing import BinaryIO
import sys

from base_coder import BaseDecoder
from utils import DECOMP_FILE_EXTENSION, BITS_PER_BYTE, PROGRESS_FILE_NAME, BYTES_PER_MB
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BIT,
    IO_MODE_BYTE,
)
from adaptive_huffman_tree import AdaptiveHuffmanTree, DECODE_MODE


class AdaptiveDecoder(BaseDecoder):
    BITS_PER_READ = 256  # more convenient to strip off dummy bits
    ALERT_PERIOD = BYTES_PER_MB

    def __init__(self, verbose: int=0):
        super().__init__(verbose)

        self._chunk_size: int
        self._shrink_factor: int

    def decode(self, src_file_path: str, decomp_file_path: str):
        with open(src_file_path, "rb") as src, open(decomp_file_path, "wb") as decomp:
            self._parse_header(src)
            tree = AdaptiveHuffmanTree(self._bytes_per_symbol, DECODE_MODE, self._chunk_size, self._shrink_factor)

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
                        self._symbol_cnt += 1

                        if self._should_alert():
                            self._export_progress()

        self._trunc(decomp_file_path)

    def _export_progress(self):
        with open(PROGRESS_FILE_NAME, "w") as f:
            f.write(f"{self._symbol_cnt * self._bytes_per_symbol // self.ALERT_PERIOD} Mb compressed\n")
        
        self._alert_cnt += 1

    def _parse_header(self, file_obj: BinaryIO):
        """
            bits per symbol: 1 byte
            dummy codeword bits: 1 byte
            dummy codeword bytes: 1 byte
            shrink period (Mb): 1 byte
            shrink factor: 1 byte
        """

        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)
        self._bits_per_symbol = ord(stream.read(1))
        assert self._bits_per_symbol > 0 and self._bits_per_symbol % 8 == 0
        self._bytes_per_symbol = self._bits_per_symbol // BITS_PER_BYTE

        self._dummy_codeword_bits = ord(stream.read(1))
        assert 0 <= self._dummy_codeword_bits < BITS_PER_BYTE

        self._dummy_symbol_bytes = ord(stream.read(1))
        assert 0 <= self._dummy_symbol_bytes < self._bytes_per_symbol

        self._chunk_size = ord(stream.read(1))
        self._shrink_factor = ord(stream.read(1))


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])
    
    verbose = int(kwargs.get("v", 0))
    decoder = AdaptiveDecoder(verbose)

    src = kwargs["in"]
    decomp = kwargs.get("out", f"{src}.{DECOMP_FILE_EXTENSION}")
    decoder.decode(src, decomp)
