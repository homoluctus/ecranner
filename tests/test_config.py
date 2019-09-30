import os
import pathlib
import pytest
from ecranner.config.config import (
    YAMLLoader, EnvFileLoader, FileLoader,
    load_yaml, load_dot_env
)
from ecranner.config.exceptions import (
    ConfigurationError, EnvFileNotFoundError,
    ConfigurationNotFoundError
)


@pytest.fixture()
def file_loader():
    return FileLoader('tests/assets/test_valid.yml')


class TestFileLoader:
    def test_filepath(self, file_loader):
        path = file_loader.filepath

        assert isinstance(path, pathlib.Path) is True
        assert str(path) == file_loader.filename

    def test_find(self):
        target_file = 'tests/assets/test_valid.yml'
        result = FileLoader._find(target_file)
        assert result == target_file

    def test_find_default_filename(self):
        target_file = 'tests/assets/test_valid.yml'
        expected_result = str(pathlib.Path.cwd().joinpath(target_file))
        result = FileLoader._find('', default_filename=target_file)
        assert result == expected_result

    def test_find_invalid(self):
        result = FileLoader._find('NOT_FOUND')
        assert result is False

    def test_exists(self):
        target_file = 'tests/assets/test_valid.yml'
        result = FileLoader.exists(target_file)
        assert result is True

    def test_exists_return_false(self):
        target_file = 'NOT_FOUND'
        result = FileLoader.exists(target_file)
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

        with pytest.raises(ConfigurationNotFoundError):
            loader.load()

    def test_default_config_path(self):
        expected_path = pathlib.Path.cwd().joinpath('ecranner.yml')
        result = YAMLLoader.default_config_path()
        assert result == expected_path


class TestEnvFileLoader:
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

    def test_default_dot_env_path(self):
        expected_path = pathlib.Path.cwd().joinpath('.env')
        result = EnvFileLoader.default_dot_env_path()
        assert result == expected_path


def test_load_yaml():
    expected_result = {
        'aws':
        {
            'prod': {
                'account_id': 472834287103,
                'aws_access_key_id': 'vjlskd896754cs',
                'aws_secret_access_key': 'vcjsdkl739824as',
                'images': ['image:1.4', 'image:5.3'],
                'region': 'us-east-1'
            },
            'stg': {
                'account_id': 111111111111,
                'aws_access_key_id': 'jsodlc8434fs',
                'aws_secret_access_key': 'jsodlc8cvsd434fs',
                'images': ['image:latest', 'image:1.0-dev'],
                'region': 'us-east-1'
            }
        },
        'trivy': {
            'options': '--severity CRITICAL -q',
            'path': '~/user/.local/bin/trivy'
        },
        'version': '1.0'
    }

    config_filepath = 'tests/assets/validation/valid_config.yml'
    result = load_yaml(config_filepath)
    assert result == expected_result


def test_load_yaml_default():
    expected_result = {
        'aws':
        {
            'prod': {
                'account_id': 472834287103,
                'aws_access_key_id': 'vjlskd896754cs',
                'aws_secret_access_key': 'vcjsdkl739824as',
                'images': ['image:1.4', 'image:5.3'],
                'region': 'us-east-1'
            },
            'stg': {
                'account_id': 111111111111,
                'aws_access_key_id': 'jsodlc8434fs',
                'aws_secret_access_key': 'jsodlc8cvsd434fs',
                'images': ['image:latest', 'image:1.0-dev'],
                'region': 'us-east-1'
            }
        },
        'trivy': {
            'options': '--severity CRITICAL -q',
            'path': '~/user/.local/bin/trivy'
        },
        'version': '1.0'
    }
    result = load_yaml()
    assert isinstance(result, dict)
    assert result == expected_result


def test_load_yaml_not_found():
    with pytest.raises(ConfigurationNotFoundError):
        load_yaml('NOT_FOUND')


def test_load_dot_env():
    dot_env_filepath = 'tests/assets/.valid_env'
    result = load_dot_env(dot_env_filepath)
    assert result is True


def test_load_dot_env_default():
    result = load_dot_env()
    assert result is True


def test_load_dot_env_default_not_found():
    bk_file = '.env.test_bk'
    dot_env_path = pathlib.Path(EnvFileLoader.DEFAULT_FILENAME)
    if dot_env_path.exists():
        dot_env_path.rename(bk_file)

    result = load_dot_env()
    assert result is False

    if EnvFileLoader.exists(bk_file):
        pathlib.Path(bk_file).rename(EnvFileLoader.DEFAULT_FILENAME)


def test_load_dot_env_not_found():
    with pytest.raises(EnvFileNotFoundError):
        load_dot_env('NOT_FOUND')
