import os
import yaml
from pathlib import Path

from .log import get_logger
from .exceptions import (
    ConfigurationError, NotAFileError
)


logger = get_logger()


class FileLoader:
    """Base class to load file"""

    def __init__(self, filename):
        self.filename = filename

    @staticmethod
    def exists(filename):
        """Check if filename exists

        Args:
            filename (str, pathlib.Path)

        Returns:
            True: File exists

        Raises:
            TypeError
            FileNotFoundError
            NotAFileError
        """

        if not isinstance(filename, (Path, str)):
            raise TypeError('Expected pathlib.Path or str object')

        if not isinstance(filename, Path):
            filename = Path(filename)

        if not filename.exists():
            raise FileNotFoundError(f'{filename} does not exist')

        if not filename.is_file():
            raise NotAFileError(f'{filename} is not a file')

        logger.debug(f'{filename} exists and is a file')
        return True

    def load(self):
        """Load a file"""

        raise NotImplementedError()

    @property
    def filepath(self):
        """Convert from filename to pathlib.Path instance

        Retuns:
            pathlib.Path instance
        """

        return Path(self.filename)


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
    def __init__(self, filename=''):
        super().__init__(filename)
        self.env_vars = {}

    def find(self):
        """Find dot env file

        Returns:
            filename (str): path to dot env file if find
        """

        if self.filename == '':
            self.filename = str(Path.cwd().joinpath('.env'))

        if self.exists():
            return self.filename

    def load(self):
        """Load env file

        Returns:
            True

        Raises:
            FileNotFoundError
            ConfigurationError
        """

        if not self.is_hidden():
            logger.warning('env_file should be as a hidden file')

        try:
            with open(self.filename) as f:
                lines = f.read()

        except FileNotFoundError as err:
            raise err

        except Exception as err:
            raise ConfigurationError(f'{err.__class__.__name__}: {err}')

        logger.debug(f'Loaded environment variables from {self.filename}')

        for line in lines:
            key, value = line.split('=')
            self.env_vars[key] = value

        return True

    def set_env(self, override=False):
        """Set as environment variable

        Args:
            override (boolean): allow to override existing environment variable

        Returns:
            True
        """

        for key, value in self.env_vars.items():
            if key in os.environ and not override:
                continue

            os.environ[key] = value

        return True

    def is_hidden(self):
        """Check if self.filename is hidden file

        Returns:
            boolean
        """

        try:
            self.exists()
        except Exception as err:
            raise err

        suffix_filename = self.filepath.name

        if not suffix_filename.startswith('.'):
            return False

        return True
