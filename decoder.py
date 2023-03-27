from typing import Optional
from io import BufferedReader
 
from bit_io_stream import BitInStream, BitOutStream, IO_MODE_BIT, IO_MODE_BYTE, BITS_PER_BYTE
from huffman_tree import HuffmanTree


class Decoder:
    def __init__(self):
        self._bits_per_symbol: int
        self.BYTES_PER_READ: int
        self._dummy_symbol_bytes: int
        self._dummy_codeword_bits: int
        self._tree: HuffmanTree

    def decode(self, src_file_path, decomp_file_path: Optional[str]=None):
        if decomp_file_path is None:
            decomp_file_path = f"{src_file_path}.decomp"

        with open(src_file_path, "rb") as src, open(decomp_file_path, "wb") as decomp:
            self._parse_header(src)

            istream = BitInStream(src, mode=IO_MODE_BIT)
            ostream = BitOutStream(decomp, mode=IO_MODE_BYTE)

            next_bit_seq = self._get_bit_seuence(istream)
            while next_bit_seq:
                curr_bit_seq = next_bit_seq
                next_bit_seq = self._get_bit_seuence(istream)

                if not next_bit_seq and self._dummy_codeword_bits > 0:
                    curr_bit_seq = curr_bit_seq[:-self._dummy_codeword_bits]

                for order in self._tree.decode(curr_bit_seq):
                    symbol = chr(order)
                    ostream.write(symbol)

    def _parse_header(self, file_obj: BufferedReader):
        # {bits per symbol}{dummy symbol bytes}{code length table}{dummy codeword bits}

        stream = BitInStream(file_obj, mode=IO_MODE_BYTE)

        self._bits_per_symbol = stream.read()
        self.BYTES_PER_READ = self._bits_per_symbol // BITS_PER_BYTE
        
        self._dummy_symbol_bytes = stream.read()

        code_len_table = [
            stream.read() 
            for _ in range(2 ** self._bits_per_symbol)
        ]

        self._dummy_codeword_bits = stream.read()

        self._tree = HuffmanTree(code_len_table=code_len_table)
        self._code_dict = self._tree.code_dict  # for debug purpose

    def _get_bit_seuence(self, stream: BitInStream) -> str:
        seq = ""
        for _ in range(BITS_PER_BYTE):
            bit = stream.read()
            if bit == BitInStream.EOF:
                return ""
            
            seq += str(bit)

        assert len(seq) == BITS_PER_BYTE
        return seq
