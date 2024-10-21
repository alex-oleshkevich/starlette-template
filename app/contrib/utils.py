from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Get client IP address from the request."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    if request.client:
        return request.client.host
    raise ValueError("Cannot get client IP address from the request.")
