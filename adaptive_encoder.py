import sys
from pathlib import Path

from base_coder import BaseEncoder
from utils import BITS_PER_BYTE, COMP_FILE_EXTENSION, PROGRESS_FILE_NAME, BYTES_PER_MB
from bit_io_stream import (
    BitInStream,
    BitOutStream,
    IO_MODE_BYTE,
    IO_MODE_BIT,
)
from adaptive_huffman_tree import AdaptiveHuffmanTree, ENCODE_MODE


class AdaptiveEncoder(BaseEncoder):
    ALERT_PERIOD = BYTES_PER_MB

    def __init__(self, bytes_per_symbol: int, verbose: int=0, chunk_size: int = 0, shrink_factor: int = 2):
        super().__init__(bytes_per_symbol, verbose)

        assert 0 <= chunk_size < 2 ** BITS_PER_BYTE
        assert 1 < shrink_factor < 2 ** BITS_PER_BYTE
        self._chunk_size: int = chunk_size
        self._shrink_factor: int = shrink_factor
    
    @property
    def avg_code_len(self) -> float:
        return self._bits_written / self._symbol_cnt

    def encode(self, src_file_path: str, comp_file_path: str):
        with open(comp_file_path, "wb") as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(chr(0) * self._get_header_size()) # preserve space for header

        self._write_content(src_file_path, comp_file_path)
        self._write_header(comp_file_path)

    def export_results(self, export_path: Path):
        with open(export_path, "w") as f:
            f.write(f"{'='*10} params {'='*10}\n")
            f.write(f"bytes per symbol: {self._bytes_per_symbol}\n")
            f.write(f"chunk size: {chunk_size}\n")
            f.write(f"shrink factor: {self._shrink_factor}\n")

            f.write(f"\n{'='*10} statistics {'='*10}\n")
            f.write(f"total symbols: {self._symbol_cnt}\n")
            f.write(f"average codeword length: {self.avg_code_len}\n")
            f.write(f"compression ratio: {self.compression_ratio}\n")
            f.write(f"shrink counts: {self._tree.shrink_cnt}\n")

    def _export_progress(self):
        with open(PROGRESS_FILE_NAME, "w") as f:
            f.write(f"{self._symbol_cnt * self._bytes_per_symbol // self.ALERT_PERIOD} Mb compressed\n")
            f.write(f"Average codeword length: {self.avg_code_len} bits\n")
        
        self._alert_cnt += 1

    def _write_header(self, comp_file_path: str):
        assert 0 <= self._dummy_codeword_bits < BITS_PER_BYTE

        """
            bits per symbol: 1 byte
            dummy codeword bits: 1 byte
            dummy codeword bytes: 1 byte
            shrink period (Mb): 1 byte
            shrink factor: 1 byte
        """

        with open(comp_file_path, "r+b") as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(chr(self._bits_per_symbol))
            stream.write(chr(self._dummy_codeword_bits))
            stream.write(chr(self._dummy_symbol_bytes))
            stream.write(chr(self._chunk_size))
            stream.write(chr(self._shrink_factor))

    def _write_content(self, src_file_path: str, comp_file_path: str):
        self._tree = AdaptiveHuffmanTree(self._bytes_per_symbol, ENCODE_MODE, self._chunk_size)
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

                for bit in self._tree.encode(symbol):
                    ostream.write(bit)
                    self._bits_written += 1

                self._export_progress()

            trailing_bits = ostream.flush()
            self._dummy_codeword_bits = 0 if trailing_bits == 0 else BITS_PER_BYTE - trailing_bits

    def _get_header_size(self):
        return 5


if __name__ == "__main__":
    kwargs = dict([arg.split("=") for arg in sys.argv[1:]])

    export_path = kwargs.get("export", None)
    if export_path:
        export_path = Path(export_path)
        if export_path.exists():
            raise AssertionError(f"{export_path} already exists!")

    bytes_per_symbol = int(kwargs.get("b", 1))
    verbose = int(kwargs.get("v", 0))
    chunk_size = int(kwargs.get("K", 0))
    shrink_factor = int(kwargs.get("alpha", 2))

    src = kwargs["in"]
    comp = kwargs.get("out", f"{src}.{COMP_FILE_EXTENSION}")

    encoder = AdaptiveEncoder(bytes_per_symbol, verbose, chunk_size, shrink_factor)
    encoder.encode(src, comp)

    if export_path:
        encoder.export_results(export_path)
