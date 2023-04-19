from math import ceil
import io

from utils import MAX_BYTE_PER_SYMBOL, BITS_PER_BYTE, BYTES_PER_MB

class BaseCoder:
    ALERT_PERIOD = BYTES_PER_MB

    def __init__(self, verbose):
        self._verbose = verbose

        # ===== settings =====
        self._bits_per_symbol: int = None
        self._bytes_per_symbol: int = None

        # ===== dummies =====
        self._dummy_symbol_bytes: int = 0   # (total_bytes + dummy_symbol_bytes) % bytes_per_symbol must be 0
        self._dummy_codeword_bits: int = 0  # (bits_of_encoded_content + dummy_codeword_bits) % bits_per_byte must be 0

        # ===== statistics =====
        self._symbol_cnt: int = 0

        # ===== alert =====
        self._alert_cnt: int = 0

    def _should_alert(self) -> bool:
        return self._verbose > 0 and self._symbol_cnt * self._bytes_per_symbol > self.ALERT_PERIOD * (self._alert_cnt+1)


class BaseEncoder(BaseCoder):
    def __init__(self, bytes_per_symbol: int, verbose: int):
        assert 0 < bytes_per_symbol <= MAX_BYTE_PER_SYMBOL
        super().__init__(verbose)

        self._bytes_per_symbol = bytes_per_symbol
        self._bits_per_symbol = bytes_per_symbol * BITS_PER_BYTE

        self._bits_written: int = 0   # bits written to the zipped file

    @property
    def compression_ratio(self) -> float:
        output_size = ceil(self._bits_written / BITS_PER_BYTE)
        output_size += self._get_header_size()

        return 1 - output_size / self._get_total_bytes()

    def _write_header(self, comp_file_path: str):
        raise NotImplementedError
    
    def _write_content(self, src_file_path: str, comp_file_path: str):
        raise NotImplementedError

    def _get_header_size(self) -> int:
        raise NotImplementedError
    
    def _get_total_bytes(self) -> int:
        return self._symbol_cnt * self._bytes_per_symbol - self._dummy_symbol_bytes


class BaseDecoder(BaseCoder):
    def __init__(self, verbose: int):
        super().__init__(verbose)

    def _parse_header(self, file_obj):
        raise NotImplementedError

    def _trunc(self, decomp_file_path: str):
        # strip off dummy symbol bytes
        if self._dummy_symbol_bytes == 0:
            return

        with open(decomp_file_path, "r+b") as f:
            f.seek(-self._dummy_symbol_bytes, io.SEEK_END)
            f.truncate()
