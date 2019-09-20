import os
import yaml
from pathlib import Path

from .log import get_logger
from .exceptions import ConfigurationError, EnvFileNotFoundError


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

    def find(self, default_filename=''):
        """Find dot env file

        Returns:
            filename (str): if the filename is found

        Raises:
            FileNotFoundError
        """

        if self.filename == '' and default_filename != '':
            self.filename = str(Path.cwd().joinpath(default_filename))

        if not self.exists():
            raise FileNotFoundError(f'{self.filename} could not be found')

        return self.filename

    def exists(self):
        """Check if self.filename exists and is a file

        Returns:
            boolean
        """

        path = self.filepath

        if not path.exists() or not path.is_file():
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
        """

        try:
            with open(self.filename) as f:
                return yaml.safe_load(f)

        except FileNotFoundError as err:
            raise err

        except Exception as err:
            raise ConfigurationError(f'{err.__class__.__name__}: {err}')

        else:
            logger.debug(f'Loaded configuration from {repr(self.filename)}')


class EnvFileLoader(FileLoader):
    def __init__(self, filename='.env'):
        super().__init__(filename)

    def load(self):
        """Load env file

        Returns:
            env_vars (dict)

        Raises:
            FileNotFoundError
            ConfigurationError
        """

        if not self.is_hidden():
            logger.warning(
                f'env_file {repr(self.filename)} should be as a hidden file'
            )

        if not self.exists():
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
            env (str)

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
            key (str)
            value (str)
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
            env_vars (dict): dict object stored envrionment variable

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

        if not self.exists():
            return False

        suffix_filename = self.filepath.name

        if not suffix_filename.startswith('.'):
            return False

        return True
