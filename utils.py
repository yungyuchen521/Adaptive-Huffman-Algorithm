BITS_PER_BYTE = 8
BUFFER_SIZE = 256 * 1024
MAX_BYTE_PER_SYMBOL = 8

COMP_FILE_EXTENSION = "comp"
DECOMP_FILE_EXTENSION = "decomp"
PROGRESS_FILE_NME = "progress.txt"


def extended_ord(string: str) -> int:
    order = 0

    for s in string:
        order <<= BITS_PER_BYTE
        order += ord(s)
    
    return order

def extended_chr(order: int, bits_per_symbol: int) -> str:
    assert bits_per_symbol % BITS_PER_BYTE == 0
    symbol = ""

    for _ in range(bits_per_symbol//BITS_PER_BYTE):
        symbol = f"{chr(order % 2**BITS_PER_BYTE)}{symbol}"
        order >>= BITS_PER_BYTE

    assert order == 0
    return symbol
