import os
import pathlib
import pytest
from ecranner.config import (
    YAMLLoader, EnvFileLoader, FileLoader
)
from ecranner.exceptions import (
    ConfigurationError, EnvFileNotFoundError
)


@pytest.fixture()
def file_loader():
    return FileLoader('tests/assets/test_valid.yml')


class TestFileLoader:
    def test_filepath(self, file_loader):
        path = file_loader.filepath

        assert isinstance(path, pathlib.Path) is True
        assert str(path) == file_loader.filename

    def test_find(self, file_loader):
        result = file_loader.find()
        assert result == 'tests/assets/test_valid.yml'

    def test_find_default_filename(self):
        file_loader = FileLoader('')
        target_file = 'tests/assets/test_valid.yml'
        result = file_loader.find(default_filename=target_file)
        assert result == str(pathlib.Path(target_file).absolute())

    def test_find_invalid(self):
        file_loader = FileLoader('NOT_FOUND')
        with pytest.raises(FileNotFoundError):
            file_loader.find()

    def test_exists(self, file_loader):
        result = file_loader.exists()
        assert result is True

    def test_exists_return_false(self):
        file_loader = FileLoader('NOT_FOUND')
        result = file_loader.exists()
        assert result is False


class TestYAMLLoader:
    def test_load(self):
        expected_result = {
            'test': {
                'this': ['is', 'a', 'test']
            },
            'hello': 'world'
        }
        loader = YAMLLoader('tests/assets/test_valid.yml')
        result = loader.load()

        assert result == expected_result

    def test_load_invalid(self):
        loader = YAMLLoader('tests/assets/test_invalid.yml')

        with pytest.raises(ConfigurationError):
            loader.load()

    def test_load_nonexistance(self):
        loader = YAMLLoader('NOT_FOUND.yml')

        with pytest.raises(FileNotFoundError):
            loader.load()


class Test_EnvFileLoader:
    def test_load(self):
        expected_env_vars = {
            'TEST': 'THIS_IS_TEST',
            'HELLO': 'WORLD=!'
        }
        loader = EnvFileLoader('tests/assets/.valid_env')
        env_vars = loader.load()

        assert isinstance(env_vars, dict)
        assert env_vars == expected_env_vars

    def test_load_nonexistance(self):
        loader = EnvFileLoader('NOT_FOUND')
        with pytest.raises(EnvFileNotFoundError):
            loader.load()

    def test_set_env(self):
        loader = EnvFileLoader('tests/assets/.valid_env')
        env_vars = loader.load()
        result = loader.set_env_from_dict(env_vars)

        assert result is True
        assert os.environ['TEST'] == 'THIS_IS_TEST'
        assert os.environ['HELLO'] == 'WORLD=!'
