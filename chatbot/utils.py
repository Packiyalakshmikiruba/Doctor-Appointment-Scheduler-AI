import re


def extract_time(text):

    text = text.lower()

    match = re.search(r"(\\d{1,2})[:.](\\d{2})", text)

    if match:

        hour = int(match.group(1))

        minute = int(match.group(2))

        if hour < 8:

            hour += 12

        return f"{hour:02}:{minute:02}"

    return None


def is_confirmation(text):

    text = text.lower()

    confirmations = [

        "yes",

        "ok",

        "confirm",

        "book",

        "book pannunga",

        "confirm pannunga",

        "sure",

        "continue",

        "seri",

    ]

    return any(word in text for word in confirmations)