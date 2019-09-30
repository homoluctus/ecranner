import pytest
import logging
from jsonschema import Draft7Validator

from ecranner.config.config import load_yaml
from ecranner.config.validate import validate, Schema
from ecranner.config.exceptions import (
    SchemaFileNotFoundError, ConfigSyntaxError
)


logger = logging.getLogger(__name__)


def json_schema(version):
    return Schema(version).load()


class TestValidation:
    def test_json_schemas(self):
        versions = ['1.0']
        for version in versions:
            schema = json_schema(version)
            result = Draft7Validator.check_schema(schema)
            assert result is None

    def test_validate_config(self):
        config = load_yaml('tests/assets/validation/valid_config.yml')
        result = validate(config)
        assert result is True

    def test_validate_parameter_error_config(self):
        config = load_yaml(
            'tests/assets/validation/parameter_error_config.yml')
        with pytest.raises(ConfigSyntaxError):
            validate(config)

    def test_validate_version_error_config(self):
        config = load_yaml('tests/assets/validation/version_error_config.yml')
        with pytest.raises(ConfigSyntaxError):
            validate(config)

    def test_schema_version_mismatch(self):
        config = load_yaml(
            'tests/assets/validation/version_mismatch_config.yml')
        with pytest.raises(SchemaFileNotFoundError):
            validate(config)
