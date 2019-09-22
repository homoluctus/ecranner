import os
import pytest
from ecranner.ecr import (
    ECRHandler, extract_credentials,
    set_credentials_as_env
)
from docker.errors import APIError as DockerAPIError


class TestECRHandler:
    def test_extract_account_id(self):
        expected_result = '01234567'
        registry_url = 'https://01234567.dkr.ecr.us-west-2.amazonaws.com'
        result = ECRHandler.extract_account_id(registry_url)
        assert result == expected_result

#     def test_pull(self):
#         # condition: 'alpine:latest' image must not exist
#         image_name = 'alpine:latest'
#         client = ECRHandler()
#         result = client.pull(image_name)

#         assert result == image_name

#         client.remove(image_name)
#         client.docker_client.close()

#     def test_pull_nonexistant_image(self):
#         image_name = 'nonexistant_image'
#         client = ECRHandler()

#         with pytest.raises(DockerAPIError):
#             client.pull(image_name)

#         client.docker_client.close()
