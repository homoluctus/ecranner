import os
import yaml
from pathlib import Path

from .log import get_logger
from .exceptions import ConfigurationError


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
    def __init__(self, filename):
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

        if not self.exists():
            return False

        suffix_filename = self.filepath.name

        if not suffix_filename.startswith('.'):
            return False

        return True
