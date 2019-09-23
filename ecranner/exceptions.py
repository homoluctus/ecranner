class BaseError(Exception):
    """Base Exception class"""


class ImageMismatchError(BaseError):
    """Raises error when pulled image is different from expected image"""


class AuthorizationError(BaseError):
    """Raises erorr when failed to get authorization token"""


class DecodeAuthorizationTokenError(BaseError):
    """Raises error when failed to decode authorization token"""


class LoginRegistryError(BaseError):
    """Raises error when failed to login into ECR"""


class PullImageError(BaseError):
    """Raises error if failed to pull images"""


class SlackNotificationError(BaseError):
    """Raises error when a response code from Slack is not 200"""


class ConfigSyntaxError(BaseError):
    """Configuration YAML syntax error"""


class ConfigurationError(BaseError):
    """Configuration error occurs"""


class ConfigurationNotFoundError(BaseError):
    """Configuration could not be found"""


class NotAFileError(BaseError):
    """Specified filepath does not mean file"""


class EnvFileNotFoundError(BaseError):
    """Raises error when env_file could not be found"""
