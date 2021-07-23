import unicodedata


def remove_control_characters(s):
    """
    Remove control characters such as SOS and ST from a string.
    Exists in many issn.org journal title.
    """
    if s:
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
