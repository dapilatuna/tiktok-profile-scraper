
import re


def parse_view_count(display: str) -> int | None:

    value = display.strip().upper().replace(" ", "")

    match = re.fullmatch(
        r"([\d.,]+)([KMB]?)",
        value
    )

    if match is None:
        return None

    number_text, suffix = match.groups()

    if suffix:
        number_text = number_text.replace(",", ".")
    else:
        number_text = number_text.replace(",", "")

    try:
        number = float(number_text)
    except ValueError:
        return None

    multiplier = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000
    }[suffix]

    return round(number * multiplier)


def parse_metric(text):

    if text is None:
        return None

    value = str(text).strip().upper().replace(" ", "")

    match = re.fullmatch(
        r"([\d.,]+)([KMB]?)",
        value
    )

    if not match:
        return None

    number, suffix = match.groups()

    if suffix:
        number = number.replace(",", ".")
    else:
        number = number.replace(",", "")

    try:
        return round(
            float(number) * {
                "": 1,
                "K": 1000,
                "M": 1000000,
                "B": 1000000000
            }[suffix]
        )

    except ValueError:
        return None
