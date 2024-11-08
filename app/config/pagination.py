import contextlib

from starlette.requests import Request

page_size = 50
max_page_size = 100


def get_page_number(request: Request, param_name: str = "page") -> int:
    """Get page number from request query params."""
    with contextlib.suppress(ValueError):
        return max(int(request.query_params.get(param_name, 1)), 1)
    return 10


def get_page_size(request: Request, param_name: str = "page_size") -> int:
    """Get page size from request query params. Default is `page_size`, max is `max_page_size`."""
    with contextlib.suppress(ValueError):
        return min(int(request.query_params.get(param_name, page_size)), page_size)
    return page_size
