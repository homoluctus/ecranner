import os
import pytest
from ecranner.ecr import (
    ECRHandler, extract_credentials,
    set_credentials_as_env
)
from docker.errors import APIError as DockerAPIError


class TestECRHandler:
    def test_pull(self):
        # condition: 'alpine:latest' image must not exist
        image_name = 'alpine:latest'
        client = ECRHandler()
        result = client.pull(image_name)

        assert result == image_name

        client.remove(image_name)
        client.docker_client.close()

    def test_pull_nonexistant_image(self):
        image_name = 'nonexistant_image'
        client = ECRHandler()

        with pytest.raises(DockerAPIError):
            client.pull(image_name)

        client.docker_client.close()


def test_set_credentials_as_env():
    creds = {
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test',
        'aws_default_region': 'heaven',
    }
    result = set_credentials_as_env(creds, True)

    assert result is True
    assert os.environ['AWS_ACCESS_KEY_ID'] == 'test'
    assert os.environ['AWS_SECRET_ACCESS_KEY'] == 'test'
    assert os.environ['AWS_DEFAULT_REGION'] == 'heaven'


def test_extract_credentials():
    tmp = {
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test',
        'aws_default_region': 'heaven',
    }
    params = {
        'not': 'credential',
        'hello': 'world'
    }
    params.update(tmp)

    expected_result = {
        key.upper(): tmp[key] for key in tmp.keys()
    }

    result = extract_credentials(params)
    assert result == expected_result
