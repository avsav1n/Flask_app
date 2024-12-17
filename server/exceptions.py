class HttpError(Exception):
    def __init__(self, status_code: int, message: str | dict | list) -> None:
        self.status_code = status_code
        self.message = message
