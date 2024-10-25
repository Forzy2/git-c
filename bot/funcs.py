import functools
from .config import OWN_USER_ID


def is_admin(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        message = kwargs.get("message") if kwargs.get("message") else args[0]
        try:
            assert message.from_user.id in OWN_USER_ID
            
            await func(*args, **kwargs)
        except AssertionError:
            await message.answer("У тебя нету прав для использования этой команды.")
    return wrapper