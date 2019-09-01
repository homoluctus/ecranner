class BaseError(Exception):
    """Base Exception class"""


class ImageMismatchedError(BaseError):
    """Raises error when pulled image is different from expected image"""
