__all__ = ["to_upper_camel", "to_lower_camel"]


def to_upper_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


def to_lower_camel(string: str) -> str:
    upper_camel = to_upper_camel(string)
    return upper_camel[0].lower() + upper_camel[1:]
