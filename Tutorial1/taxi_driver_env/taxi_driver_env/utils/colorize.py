COLOR_2_NUM = {
    "gray": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "crimson": 38,
}


def colorize(string: str, color: str, bold: bool = False, highlight: bool = False) -> str:
    attr = []
    num = COLOR_2_NUM[color]
    if highlight:
        num += 10
    attr.append(str(num))
    if bold:
        attr.append("1")
    attrs = ";".join(attr)
    return f"\x1b[{attrs}m{string}\x1b[0m"
