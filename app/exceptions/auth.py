class InvalidTokenException(Exception):
    def __init__(self, detail: str = "Invalid or expired token"):
        self.detail = detail
