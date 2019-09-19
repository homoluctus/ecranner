class BaseError(Exception):
    """Base Exception class"""


class ImageMismatchedError(BaseError):
    """Raises error when pulled image is different from expected image"""


class DecodeAuthorizationTokenError(BaseError):
    """Raises error when failed to decode authorization token"""


class LoginRegistryError(BaseError):
    """Raises error when failed to login into ECR"""


class SlackNotificationError(BaseError):
    """Raises error when a response code from Slack is not 200"""


class ConfigSyntaxError(BaseError):
    """Configuration YAML syntax error"""


class ConfigurationError(BaseError):
    """Configuration error occurs"""
