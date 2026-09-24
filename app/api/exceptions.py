class TMDBError(Exception):
    pass


class TMDBConfigError(TMDBError):
    pass


class TMDBTimeoutError(TMDBError):
    pass


class TMDBConnectionError(TMDBError):
    pass


class TMDBAPIError(TMDBError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
