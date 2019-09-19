import docker
from docker.errors import ImageNotFound, APIError
from .log import get_logger


logger = get_logger()


class DockerHandler:
    def __init__(self, base_url=None, timeout=60):
        base_url = base_url or 'unix:///var/run/docker.sock'
        self.docker_client = docker.DockerClient(
            base_url=base_url,
            version='auto',
            timeout=timeout,
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self.docker_client.close()

    def remove(self, image_name, force=False):
        """Remove image pulled in local machine

        Args:
            image_name (str)
            force (boolean)

        Returns:
            boolean
        """

        if not isinstance(image_name, str):
            raise TypeError(f'Expected str object, \
                but {image_name} is {type(image_name)} object')

        if not self.exists(image_name):
            return True

        res = self.docker_client.images.remove(image_name, force=force)
        logger.debug(f'Response from Docker Engine: {res}')

        # Check again if specified docker image exists
        if self.exists(image_name):
            return False

        return True

    def exists(self, image_name):
        """Make sure if specified docker image exists in local

        Args:
            image_name (str)

        Returns:
            boolean

        Raises:
            docker.errors.APIError
        """

        if not isinstance(image_name, str):
            raise TypeError(f'Expected str object, \
                but argument is {type(image_name)} object')

        try:
            self.docker_client.images.get(image_name)

        except ImageNotFound:
            return False

        except APIError as err:
            raise err

        else:
            logger.debug(f'Found {repr(image_name)} Docker image')
            return True
