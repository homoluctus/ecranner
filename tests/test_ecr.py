import pytest
from ecranner.ecr import ECRHandler
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
