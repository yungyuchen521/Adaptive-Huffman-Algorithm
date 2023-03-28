from typing import Union, BinaryIO
from utils import BITS_PER_BYTE


IO_MODE_BIT = "IO_MODE_BIT"
IO_MODE_BYTE = "IO_MODE_BYTE"


class BitInStream:
    def __init__(self, file_obj: BinaryIO, mode: str):
        assert mode in (IO_MODE_BIT, IO_MODE_BYTE)
        self._mode = mode

        # to avoid "\r" -> "\n" issues
        # file_obj should be opened with "rb"
        self._file_obj: BinaryIO = file_obj
        self._byte: int = 0
        self._bits_cnt: int = 0

    def read(self, n: int=1) -> str:
        assert n > 0

        if self._mode == IO_MODE_BIT:
            if n > 1:
                print("Reading more than 1 bit at a time is not supported.")

            return self._read_bit()
        else:
            return self._read_byte(n)

    def _read_bit(self) -> str:
        if self._bits_cnt == 0:
            tmp = self._file_obj.read(1)
            if len(tmp) == 0:
                return ""

            self._byte = tmp[0] # order of the character
            self._bits_cnt = BITS_PER_BYTE

        assert 0 < self._bits_cnt <= BITS_PER_BYTE
        self._bits_cnt -= 1

        bit = (self._byte >> self._bits_cnt) & 1
        return str(bit)

    def _read_byte(self, n: int) -> str:
        tmp = self._file_obj.read(n)
        return "".join([chr(b) for b in tmp])

    def close(self):
        self._file_obj.close()

class BitOutStream:
    def __init__(self, file_obj: BinaryIO, mode: str):
        # to avoid "\r" -> "\n" issues
        # file_obj should be opened with "wb" / "ab"
        self._file_obj: BinaryIO = file_obj
        self._byte: int = 0
        self._bits_cnt: int = 0

        assert mode in (IO_MODE_BIT, IO_MODE_BYTE)
        self._mode = mode

    def write(self, b: str):
        if self._mode == IO_MODE_BIT:
            self._write_bit(b)
        else:
            self._write_byte(b)

    def flush(self) -> int:
        # return number bits flushed
        assert self._mode == IO_MODE_BIT

        if self._bits_cnt == 0:
            return 0

        bits_flushed = self._bits_cnt
        self._byte <<= (BITS_PER_BYTE - self._bits_cnt)
        output = self._to_bytes(self._byte)
        self._file_obj.write(output)

        self._bits_cnt = 0
        self._byte = 0

        return bits_flushed

    def _write_bit(self, bit: str):
        assert bit == "0" or bit == "1"
        self._byte <<= 1
        self._byte += (bit == "1")
        self._bits_cnt += 1

        if self._bits_cnt == BITS_PER_BYTE:
            output = self._to_bytes(self._byte)
            self._file_obj.write(output)
            self._byte = 0
            self._bits_cnt = 0

    def _write_byte(self, byte: str):
        for b in byte:
            output = self._to_bytes(b)
            self._file_obj.write(output)

    @staticmethod
    def _to_bytes(c: Union[str, int]) -> bytes:
        # w/o this conversion, characters whose order > 127 will not be written properly
        if isinstance(c, str):    
            assert len(c) == 1
            order = ord(c)
            return bytes((order,))
        elif isinstance(c, int):
            assert 0 <= c < 2 ** BITS_PER_BYTE
            return bytes([c])

    def close(self):
        self._file_obj.close()


if __name__ == "__main__":
    import random
    import os
    
    TEST_FILE_NAME = "test.txt"

    rand_str = "\r\n"
    for _ in range(1024):
        rand_order = random.randint(0, 2**BITS_PER_BYTE-1)
        rand_str += chr(rand_order)
    rand_str += "\n\r"

    def test_byte_io(rand_str: str):
        with open(TEST_FILE_NAME, "wb") as f:
            stream = BitOutStream(f, mode=IO_MODE_BYTE)
            stream.write(rand_str)

        with open(TEST_FILE_NAME, "rb") as f:
            stream = BitInStream(f, mode=IO_MODE_BYTE)
            string = ""

            while True:
                c = stream.read()
                if not c:
                    break

                string += c

        if string != rand_str:
            raise AssertionError(f"\norg: {rand_str}\nres: {string}")

        os.system(f"rm {TEST_FILE_NAME}")

    def test_bit_io(rand_str: str):
        def char_to_bit_seq(c: str) -> str:
            assert len(c) == 1
            bits = bin(ord(c)).split("b")[-1]
            if len(bits) != BITS_PER_BYTE:
                bits = "0"*(BITS_PER_BYTE-len(bits))+ bits
            assert len(bits) == BITS_PER_BYTE
            return bits

        with open(TEST_FILE_NAME, "wb") as f:
            stream = BitOutStream(f, mode=IO_MODE_BIT)
            for c in rand_str:
                for bit in char_to_bit_seq(c):
                    stream.write(bit)

            assert stream.flush() == 0

        with open(TEST_FILE_NAME, "rb", 1024) as f:
            stream = BitInStream(f, mode=IO_MODE_BIT)
            buffer = 0
            string = ""
            eof = False

            while not eof:
                for _ in range(BITS_PER_BYTE):
                    bit = stream.read()
                    if not bit:
                        eof = True
                        break
                    
                    assert bit in "01"
                    buffer <<= 1
                    buffer += (bit == "1")
                
                if not (0 <= buffer < 256):
                    raise AssertionError(f"buffer={buffer}")
                string += chr(buffer)
                buffer = 0

        for i, c in enumerate(rand_str):
            if c != string[i]:
                print(f"character {i} is different! org: {ord(c)}, res: {ord(string[i])}")
                raise AssertionError(f"\norg: {rand_str}\nres: {string}")

        os.system(f"rm {TEST_FILE_NAME}") 

    test_byte_io(rand_str)
    test_bit_io(rand_str)
