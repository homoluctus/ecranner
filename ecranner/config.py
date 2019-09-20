import os
import yaml
from pathlib import Path

from .log import get_logger
from .exceptions import (
    ConfigurationError, EnvFileNotFoundError,
    ConfigurationNotFoundError
)


logger = get_logger()


class FileLoader:
    """Base class to load file"""

    def __init__(self, filename):
        self.filename = filename

    @property
    def filepath(self):
        """Convert from filename to pathlib.Path instance

        Retuns:
            pathlib.Path instance
        """

        return Path(self.filename)

    @classmethod
    def _find(cls, filename, default_filename=''):
        """Find self.filename
        If self.filename is '', default_filename is set as self.filename

        Returns:
            filename (str): if the filename is found
            False: if the filename can not be found
        """

        if not filename and default_filename:
            filename = str(Path.cwd().joinpath(default_filename))

        if not cls.exists(filename):
            return False

        return filename

    @staticmethod
    def exists(filename):
        """Check if filename exists and is a file

        Args:
            filename (str, pathlib.Path)

        Returns:
            boolean
        """

        if not isinstance(filename, (str, Path)):
            logger.debug(
                f'The given argument type is {type(filename)} \
                (Expected str type)'
            )
            return False

        if isinstance(filename, str):
            filename = Path(filename)

        if not filename.exists() or not filename.is_file():
            return False

        return True

    def load(self):
        """Load a file"""

        raise NotImplementedError()


class YAMLLoader(FileLoader):
    def __init__(self, filename='ecranner.yml'):
        super().__init__(filename)

    def load(self):
        """Load configuration YAML file

        Returns:
            dict object loaded from config

        Raises:
            FileNotFoundError
            ConfigurationError: raises if exceptions except
                                FileNotFoundError occurs
            ConfigurationNotFoundError
        """

        if not self.exists(self.filename):
            raise ConfigurationNotFoundError(
                f'Could not found configuration \
                YAML file {repr(self.filename)}'
            )

        try:
            with open(self.filename) as f:
                return yaml.safe_load(f)

        except Exception as err:
            raise ConfigurationError(f'{err.__class__.__name__}: {err}')

        else:
            logger.debug(f'Loaded configuration from {repr(self.filename)}')

    @classmethod
    def find_config(cls, filename=''):
        """Find configuration YAML file

        Args:
            filename (str)

        Returns:
            filename
            False
        """

        return cls._find(filename, cls.default_config_path)

    @staticmethod
    @property
    def default_config_path():
        """Get default filename

        Returns:
            default configuration file path
        """

        return str(Path.cwd().joinpath('ecranner.yml'))


class EnvFileLoader(FileLoader):
    def __init__(self, filename='.env'):
        super().__init__(filename)

    def load(self):
        """Load env file

        Returns:
            env_vars(dict)

        Raises:
            TypeError
            FileNotFoundError
            ConfigurationError
            EnvFileNotFoundError
        """

        if not self.is_hidden():
            logger.warning(
                f'env_file {repr(self.filename)} should be as a hidden file'
            )

        if not self.exists(self.filename):
            raise EnvFileNotFoundError(
                f'Env file {repr(self.filename)} could not be found'
            )

        env_vars = {}
        with open(self.filename) as f:
            for line in f:
                line = line.strip()

                if line.startswith('#') or not line:
                    continue

                key, value = self.split_env(line)

                if key in env_vars:
                    logger.warning(
                        f'Found duplicate environment variable {repr(key)}'
                    )

                env_vars[key] = value

        logger.debug(f'Loaded environment variables from {self.filename}')
        return env_vars

    def split_env(self, env):
        """Split environment variable

        Args:
            env(str)

        Returns:
            tuple(key, value)

        Raises:
            TypeErorr
            ConfigurationError
        """

        if not isinstance(env, str):
            raise TypeError(
                f'Expected str object, but the argument is {type(env)} object')

        key, value = env.split('=', maxsplit=1)

        if ' ' in key:
            raise ConfigurationError(f'Environment variable name {repr(key)} \
                                    can not contain whitespace')

        return (key, value)

    @staticmethod
    def set_env(key, value, override=False):
        """Set as environment variable

        Args:
            key(str)
            value(str)
            override(boolean): allow to override existing environment variable.

        Returns:
            boolean:
                return True if succeed that set as a environment variable.
                return False if key is already set as environment variable
                and override option is False.
        """

        if key in os.environ and not override:
            return False

        os.environ[key] = value
        return True

    @staticmethod
    def set_env_from_dict(env_vars={}, override=False):
        """Set environment variable from dict

        Args:
            env_vars(dict): dict object stored envrionment variable

        Returns:
            boolean
        """

        if not isinstance(env_vars, dict):
            raise TypeError(
                f'Expected dict object, \
                but argument is {type(env_vars)} object'
            )

        for key, value in env_vars.items():
            EnvFileLoader.set_env(key, value, override)

        return True

    def is_hidden(self):
        """Check if self.filename is hidden file

        Returns:
            boolean
        """

        filename = self.filepath

        if not filename.name.startswith('.'):
            return False

        return True

    @classmethod
    def find_dot_env(cls, filename=''):
        """Find dot env file

        Args:
            filename(str)

        Returns:
            filename(str)
            False
        """

        return cls._find(filename, cls.default_dot_env_path)

    @staticmethod
    @property
    def default_dot_env_path():
        """Get default filename

        Returns:
            default configuration file path
        """

        return str(Path.cwd().joinpath('.env'))


def load_yaml(filename=''):
    """Load configuration from YAML file

    Args:
        filename(str)

    Returns:
        config(dict)
    """

    config_filepath = YAMLLoader.find_config(filename)

    if not config_filepath:
        raise ConfigurationNotFoundError(
            'Could not found configuration YAML file'
        )
    loader = YAMLLoader(config_filepath)
    config = loader.load()
    return config


def load_dot_env(filename=''):
    """Load dot env file and then
    set parameters as system environment variables

    Args:
        filename(str)

    Returns:
        boolean
    """

    dot_env_filepath = EnvFileLoader.find_dot_env(filename)

    if not dot_env_filepath:
        raise EnvFileNotFoundError('Could not found .env file')

    loader = EnvFileLoader(dot_env_filepath)
    env_vars = loader.load()
    return loader.set_env_from_dict(env_vars)
