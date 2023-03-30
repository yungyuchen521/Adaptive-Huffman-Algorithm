from typing import Optional
import io

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    MAX_BYTE_PER_SYMBOL,
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

    def __init__(self, period: int):
        super().__init__(period)

    def decode(self, src_file_path: str, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.decomp"
        
        dummy_bits = self._get_dummy_bits(src_file_path)

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(decomp_file_path, "wb", BUFFER_SIZE) as decomp:
            istream = BitInStream(src, mode=IO_MODE_BIT)
            ostream = BitOutStream(decomp, mode=IO_MODE_BYTE)

            next_bit_seq = istream.read(self.BITS_PER_READ)
            while next_bit_seq:
                curr_bit_seq = next_bit_seq
                next_bit_seq = istream.read(self.BITS_PER_READ)

                if 0 < len(next_bit_seq) < 64:
                    curr_bit_seq += next_bit_seq
                    next_bit_seq = None # to exit the loop

                if not next_bit_seq:
                    # the last byte, which indicates number of dummy bits, should not be included
                    curr_bit_seq = curr_bit_seq[:-dummy_bits-BITS_PER_BYTE]

                for bit in curr_bit_seq:
                    symbol = self._tree.decode(bit)
                    if symbol:
                        ostream.write(symbol)
                        self._symbol_cnt += 1
                        self._symbol_distributions[symbol] += 1

                        if self._symbol_cnt % self._period == 0:
                            self._update_tree()

    def _get_dummy_bits(self, src_file_path: str) -> int:
        # number of dummy bits is indicated by the last byte
        with open(src_file_path, "rb", BUFFER_SIZE) as f:
            stream = BitInStream(f, mode=IO_MODE_BYTE)
            f.seek(-1, io.SEEK_END)
            dummy_bits = ord(stream.read(1))

        return dummy_bits
