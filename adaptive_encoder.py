from typing import Optional

from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
)
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from base_coder import BaseAdaptiveCoder


class AdaptiveEncoder(BaseAdaptiveCoder):
    def __init__(self, period: int):
        super().__init__(period)

    def encode(self, src_file_path: str, comp_file_path: Optional[str]=None):
        if comp_file_path is None:
            comp_file_path = f"{src_file_path}.comp"

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(comp_file_path, "wb", BUFFER_SIZE) as comp:
            istream = BitInStream(src, mode=IO_MODE_BYTE)
            ostream = BitOutStream(comp, mode=IO_MODE_BIT)

            while True:
                symbol = istream.read(1)

                if len(symbol) == 0:
                    break

                self._symbol_cnt += 1
                self._symbol_distributions[symbol] += 1

                for bit in self._tree.code_dict[symbol]:
                    ostream.write(bit)
                
                if self._symbol_cnt % self._period == 0:
                    self._update_tree()

            trailing_bits = ostream.flush()
            assert 0 <= trailing_bits < BITS_PER_BYTE 
            dummy_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits

        with open(comp_file_path, "ab") as f:
            ostream = BitOutStream(f, mode=IO_MODE_BYTE)
            ostream.write(chr(dummy_bits))
