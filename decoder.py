from typing import Optional, BinaryIO
import sys
import io
 
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
    BITS_PER_READ = 256  # more convenient to strip off dummy bits
    
    def __init__(self, verbose: int=0):
        super().__init__(verbose)

    def decode(self, src_file_path, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.{DECOMP_FILE_EXTENSION}"

        with open(src_file_path, "rb", BUFFER_SIZE) as src, open(decomp_file_path, "wb", BUFFER_SIZE) as decomp:
            self._parse_header(src)

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

                ostream.write(symbols)

        self.code_dict = self._tree.code_dict
        assert self._tree._cur == self._tree._root
        self._trunc(decomp_file_path)

    def _parse_header(self, file_obj: BinaryIO):
        # {bits per symbol}{dummy symbol bytes}{size of codelen_dict}{code length dict}{dummy codeword bits}
        # {code length dict} = {symbol}{code length}{symbol}{code length}{symbol}{code length}...

        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)

        self._bits_per_symbol = ord(stream.read(1))
        self._bytes_per_symbol = self._bits_per_symbol // BITS_PER_BYTE
        self._dummy_symbol_bytes = ord(stream.read(1))
        code_len_dict_size = extended_ord(stream.read(self._bytes_per_symbol))
        if code_len_dict_size == 0:
            # 0 represents 2 ** self._bits_per_symbol
            code_len_dict_size = 2 ** self.bits_per_symbol

        code_len_dict = {}
        for _ in range(code_len_dict_size):
            symbol = stream.read(self._bytes_per_symbol)
            code_len = extended_ord(stream.read(self._bytes_per_symbol))

            # 0 represents 2 ** self._bits_per_symbol
            code_len_dict[symbol] = (2 ** self._bits_per_symbol if code_len == 0 else code_len)
        
        self._dummy_codeword_bits = ord(stream.read(1))

        self._tree = HuffmanTree(code_len_dict=code_len_dict)

    def _trunc(self, decomp_file_path: str):
        # strip off dummy symbol bytes
        if self._dummy_symbol_bytes == 0:
            return

        with open(decomp_file_path, "r+b") as f:
            f.seek(-self._dummy_symbol_bytes, io.SEEK_END)
            f.truncate()

if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])
    
    verbose = int(kwargs.get("v", 0))
    decoder = Decoder(verbose=verbose)

    src = kwargs["in"]
    decomp = kwargs.get("out", f"{src}.{DECOMP_FILE_EXTENSION}")

    decoder.decode(src, decomp)
