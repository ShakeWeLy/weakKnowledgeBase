"""Service-level errors. The app maps them to HTTP responses in main.py, so routers stay free of error branches."""


class ServiceError(Exception):
    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409


class ServiceUnavailableError(ServiceError):
    status_code = 503
