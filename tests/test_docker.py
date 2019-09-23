import os
import pytest
from ecranner.docker import DockerHandler, remove_images
from docker.errors import APIError as DockerAPIError


class TestDockerHandler:
    def test_pull(self):
        # condition: 'alpine:latest' image must not exist
        image_name = 'alpine:latest'
        with DockerHandler() as client:
            result = client.pull(image_name)
            client.remove(image_name)

        assert result == image_name

    def test_pull_nonexistant_image(self):
        image_name = 'nonexistant_image'

        with pytest.raises(DockerAPIError):
            with DockerHandler() as client:
                client.pull(image_name)

    def test_remove_images(self):
        images = ['alpine:latest', 'busybox:latest']
        with DockerHandler() as client:
            for image in images:
                client.pull(image)

        result = remove_images(images)
        assert result is True
