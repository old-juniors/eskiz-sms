import functools


def force_sync(fn):
    """
    Turn an async function to sync function:
    https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec
    """
    import asyncio

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return asyncio.get_event_loop().run_until_complete(res)
        return res

    return wrapper
