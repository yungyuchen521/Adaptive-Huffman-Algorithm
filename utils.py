BITS_PER_BYTE = 8
BUFFER_SIZE = 1024
MAX_BYTE_PER_SYMBOL = 8


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

    return symbol
