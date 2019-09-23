import docker
from docker.errors import ImageNotFound, APIError

from .log import get_logger
from .exceptions import LoginRegistryError, ImageMismatchError


logger = get_logger()


class DockerImageHandler:
    UNIX_SOCKET = 'unix:///var/run/docker.sock'

    def __init__(self, base_url=None, timeout=60):
        base_url = base_url or self.UNIX_SOCKET
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

    def pull(self, image_name, all_tags=False, username=None, password=None):
        """Pull a Docker image

        Args:
            image_name (str): Docker image name included tag to pull
            all_tags (boolean): Whether all image tags are pulled
                when no tag is specified.
                The image of `latest` tag is pulled if all is False.
            username (str)
            password (str)

        Returns:
            image (list): in case, no tag is specified and all_tags is True
            pulled_image_name (str): a docker image name pulled the registry

        Raises:
            docker.errors.APIError
            ImageMismatchError
        """

        # pre check if specified docker image is already pulled
        try:
            result = self.exists(image_name)
            if result:
                return image_name

        except APIError:
            result = False

        auth_config = None
        if username and password:
            auth_config = {'username': username, 'password': password}

        if not self.tag_exists(image_name) and not all_tags:
            self.add_tag(image_name)

        try:
            image = self.docker_client.images.pull(
                image_name,
                auth_config=auth_config
            )

        except APIError as err:
            raise err

        if isinstance(image, list):
            return image

        pulled_image_name = image.tags[0]

        if pulled_image_name != image_name:
            raise ImageMismatchError(f'''
                Pulled image: {pulled_image_name}
                Expected: {image_name}
            ''')

        logger.info(f'Pulled {image_name}')
        return pulled_image_name

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

    def remove_images(self, images, force=False):
        """Remove docker images pulled in local

        Args:
            images (list): pulled docker images
            force (boolean): force to remove

        Returns:
            True: succeed to remove all images
            failed_images (list)
        """

        failed_images = []

        for image in images:
            result = self.remove(image, force)

            if not result:
                failed_images.append(image)

        return True if not failed_images else failed_images

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

    def login(self, username, password, registry, reauth=False):
        """Login to a registry

        Args:
            username (str)
            password (str)
            registry (str)
            reauth (boolean)

        Returns:
            True

        Raises:
            LoginRegistryError
            docker.errors.APIError
        """

        try:
            res = self.docker_client.login(
                username=username,
                password=password,
                registry=registry,
                reauth=reauth
            )

        except APIError as err:
            raise LoginRegistryError(f'Failed to Login to ECR: {err}')

        else:
            logger.debug(res)
            return True

    def tag_exists(self, image_name):
        """Checks if image_name contains tag

        Args:
            image_name (str)

        Returns:
            boolean
        """

        tag_prefix = ':'

        if tag_prefix in image_name \
                and not image_name.endswith(tag_prefix):
            return True

        return False

    def add_tag(self, image_name, tag='latest'):
        """Add a tag to image name

        Args:
            image_name (str)
            tag (str)

        Returns:
            image_name
        """

        if image_name.endswith(':'):
            image_name += tag
        else:
            image_name += f':{tag}'

        return image_name
