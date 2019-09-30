import json
from pathlib import Path
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

from .exceptions import SchemaFileNotFoundError, ConfigSyntaxError


class Schema:
    def __init__(self, version):
        self.version = version

    @property
    def filepath(self):
        """Get schema filepath

        Returns:
            schema file path (str)

        Raises:
            SchemaFileNotFoundError
        """

        parent_dir = Path(__file__).parent
        schema_path = parent_dir.joinpath(f'schema_{self.version}.json')

        if not schema_path.exists():
            raise SchemaFileNotFoundError(f'Could not find {schema_path} \
                Please check the version you specified')

        return str(schema_path)

    def load(self):
        """Load JSON schema to validate configuration file

        Returns:
            schema (dict)
        """

        with open(self.filepath, encoding='utf8') as fd:
            return json.load(fd)


def validate(config):
    """Validate configuration schema

    Args:
        config (dict)

    Returns:
        True: if all procedure are passed

    Raises:
        ConfigSyntaxError
        SchemaFileNotFoundError
    """

    try:
        version = config['version']
    except KeyError:
        raise ConfigSyntaxError('The "version" parameter is missing. \
            Please configure configuration version')

    try:
        schema = Schema(version).load()
    except SchemaFileNotFoundError as err:
        raise err

    try:
        Draft7Validator(schema).validate(config)
    except ValidationError as err:
        raise ConfigSyntaxError(f'Configuration syntax error occurs: {err}')

    return True
