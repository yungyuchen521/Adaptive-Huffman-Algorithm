from typing import Optional, BinaryIO
 
from base_coder import BaseStaticCoder
from utils import (
    BITS_PER_BYTE,
    BUFFER_SIZE,
    DECOMP_FILE_EXTENSION,
    extended_ord,
)
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BIT,
    IO_MODE_BYTE,
)
from huffman_tree import HuffmanTree


class Decoder(BaseStaticCoder):
    BITS_PER_READ = 256  # more convenient to strip off dummy bits & dummy bytes
    
    def __init__(self, verbose: int=0):
        super().__init__(verbose)

    def decode(self, src_file_path, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.{DECOMP_FILE_EXTENSION}"

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(decomp_file_path, "wb", BUFFER_SIZE) as decomp:
            self._parse_header(src)

            if self._verbose > 0:
                self._logger.warning(f"{self.__class__.__name__} decompressing...")

            istream = BitInStream(src, mode=IO_MODE_BIT)
            ostream = BitOutStream(decomp, mode=IO_MODE_BYTE)

            next_bit_seq = istream.read(self.BITS_PER_READ)
            while next_bit_seq:
                curr_bit_seq = next_bit_seq
                next_bit_seq = istream.read(self.BITS_PER_READ)

                if not next_bit_seq and self._dummy_codeword_bits > 0:
                    curr_bit_seq = curr_bit_seq[:-self._dummy_codeword_bits]

                symbols = ""
                for bit in curr_bit_seq:
                    symbol = self._tree.decode(bit)
                    if symbol:
                       symbols += symbol

                if not next_bit_seq and self._dummy_symbol_bytes > 0:
                    symbols = symbols[:-self._dummy_symbol_bytes]

                ostream.write(symbols)

        self.code_dict = self._tree.code_dict
        assert self._tree._cur == self._tree._root

    def _parse_header(self, file_obj: BinaryIO):
        if self._verbose > 0:
            self._logger.warning(f"{self.__class__.__name__} parsing header...")

        # {bits per symbol}{dummy symbol bytes}{code length table}{dummy codeword bits}

        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)

        self._bits_per_symbol = ord(stream.read(1))
        self._bytes_per_symbol = self._bits_per_symbol // BITS_PER_BYTE
        
        self._dummy_symbol_bytes = ord(stream.read(1))

        code_len_table = [
            extended_ord(stream.read(self._bytes_per_symbol))
            for _ in range(2 ** self._bits_per_symbol)
        ]

        self._dummy_codeword_bits = ord(stream.read(1))

        self._tree = HuffmanTree(code_len_table=code_len_table)
