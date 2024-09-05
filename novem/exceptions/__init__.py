class NovemException(Exception):
    pass


class Novem404(NovemException):
    def __init__(self, message: str):

        # 404 errors can occur if users are not authenticated, let them know
        # future improvement: consider requesting a fixed endpoint (like
        # whoami) and notify if not authenticated
        message = f"Resource not found: {message} (Are you authenticated?)"

        super().__init__(message)


class Novem403(NovemException):
    pass


class Novem401(NovemException):
    pass


