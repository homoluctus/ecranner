class BaseError(Exception):
    """Base Exception class"""


class ImageMismatchedError(BaseError):
    """Raises error when pulled image is different from expected image"""


class DecodeAuthorizationTokenError(BaseError):
    """Raises error when failed to decode authorization token"""


class LoginRegistryError(BaseError):
    """Raises error when failed to login into ECR"""