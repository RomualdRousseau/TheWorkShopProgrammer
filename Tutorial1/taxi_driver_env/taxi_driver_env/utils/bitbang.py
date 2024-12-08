def bit_set(num: int, pos: int) -> int:
    return num | (1 << pos)


def bit_set_if(num: int, pos: int, pred: bool) -> int:
    return bit_set(num, pos) if pred else bit_unset(num, pos)


def bit_unset(num: int, pos: int) -> int:
    return num & ~(1 << pos)


def is_bit_set(num: int, pos: int) -> bool:
    return bool(num & (1 << pos))
