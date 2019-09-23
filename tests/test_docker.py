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

    def test_exists(self):
        image = 'alpine:latest'
        with DockerHandler() as client:
            client.pull(image)
            result = client.exists(image)
            client.remove(image)

        assert result is True

    def test_exists_noexistance_image(self):
        with DockerHandler() as client:
            result = client.exists('not_found')

        assert result is False

    def test_exists_api_error(self):
        with pytest.raises(DockerAPIError):
            with DockerHandler() as client:
                client.exists('ERROR')