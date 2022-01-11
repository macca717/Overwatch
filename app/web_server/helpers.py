from typing import List, Literal, TypedDict
from starlette.requests import Request


__all__ = ["get_flash_messages"]


SESSION_KEY = "_messages"


Levels = Literal["is-danger", "is-warning", "is-info", "is-success"]


class FlashMessage(TypedDict):
    message: str
    category: Levels


def flash(
    request: Request,
    message: str,
    category: Levels = "is-danger",
):
    """Flash a message to the user

    Args:
        request (Request): Request instance
        message (str): Message to display
        category (str, optional): Message category ("is-danger", "is-warning", "is-info", "is-success"). Defaults to "is-danger".
    """
    if SESSION_KEY not in request.session:
        request.session[SESSION_KEY] = []
    request.session[SESSION_KEY].append(
        FlashMessage(message=message, category=category)
    )


def get_flash_messages(request: Request) -> List[FlashMessage]:
    """Retrieve the stored flash messages

    Args:
        request (Request): Request instance

    Returns:
        List[FlashMessage]: List of flash messages
    """
    if SESSION_KEY in request.session:
        return request.session.pop(SESSION_KEY)
    return []
