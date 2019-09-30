class ConfigBaseError(Exception):
    """Base class"""


class SchemaFileNotFoundError(ConfigBaseError):
    """Raise error when didn't find schema file"""


class ConfigSyntaxError(ConfigBaseError):
    """Configuration YAML syntax error"""


class ConfigurationError(ConfigBaseError):
    """Configuration error occurs"""


class ConfigurationNotFoundError(ConfigBaseError):
    """Configuration could not be found"""


class NotAFileError(ConfigBaseError):
    """Specified filepath does not mean file"""


class EnvFileNotFoundError(ConfigBaseError):
    """Raises error when env_file could not be found"""
