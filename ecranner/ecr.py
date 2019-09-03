import os
import sys
import base64
import boto3
import docker
from . import log, msg
from .exceptions import ImageMismatchedError


LOGGER = log.get_logger()


try:
    AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    IMAGE_TAG = os.getenv('IMAGE_TAG', 'latest')
except KeyError:
    LOGGER.exception(f'"AWS_ACCOUNT_ID": {msg.ENV_CONFIGURE}')
    sys.exit(1)


def pull_images():
    """Pull Docker images in AWS ECR

    Returns:
        pulled_image_list (list): returns empty list if failed to pull
                                  docker image or target image does not exist
    """

    pulled_image_list = []

    try:
        with ECRHandler() as ecr:
            auth_data = ecr.authorize()
            ecr.login(**auth_data)
            image_list = ecr.get_image_uris_filtered_by_tag(IMAGE_TAG)
            for image_name in image_list:
                ecr.pull(
                    image_name,
                    auth_data['username'],
                    auth_data['password']
                )
                LOGGER.info(f'Pulled {image_name}')
                pulled_image_list.append(image_name)

    except Exception as err:
        LOGGER.error(err, exc_info=True)

    return pulled_image_list


class ECRHandler:
    def __init__(self):
        self.ecr_client = boto3.client('ecr')
        self.params = {'registryId': AWS_ACCOUNT_ID}
        self.docker_client = docker.DockerClient(
            base_url='unix:///var/run/docker.sock',
            version='auto',
            timeout=60,
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.docker_client.close()

    def pull(self, image_name, username=None, password=None):
        """Pull Docker image

        Args:
            image_name (str): Docker image name (includes tag)
            username (str)
            password (str)

        Returns:
            image_name (str): docker image name
        """

        try:
            # pre check if specified docker image is already pulled
            self.docker_client.images.get(image_name)
            return image_name

        except (docker.errors.ImageNotFound,
                docker.errors.APIError):
            pass

        if username and password:
            auth_config = {
                'username': username,
                'password': password
            }
        else:
            auth_config = None

        try:
            image = self.docker_client.images.pull(
                image_name,
                auth_config=auth_config
            )

            pulled_image_name = image.tags[0]

            if pulled_image_name != image_name:
                raise ImageMismatchedError(f'''
                    Pulled image: {pulled_image_name}
                    But expected: {image_name}
                ''')

            return pulled_image_name

        except (docker.errors.APIError,
                ImageMismatchedError) as err:
            raise err

    def __decode_token(self, token):
        """Decode AWS ECR access token

        Args:
            token (str): AWS ECR access token (format: base64)

        Raises:
            TypeError: raises when token is not bytes object
        """

        if not isinstance(token, str):
            raise TypeError(
                f'Expected bytes object but current object is {type(token)}')

        bytes_token = base64.b64decode(token)
        return bytes_token.decode('utf-8')

    def authorize(self):
        """Get AWS ECR authorization access token

        Returns:
            authorization_data (dict): includes username, password and registry

        Raises:
            Exception
        """

        try:
            res = self.ecr_client.get_authorization_token(
                registryIds=[self.params['registryId']]
            )

            access_token = self.__decode_token(
                res['authorizationData'][0]['authorizationToken'])
            registry_url = res['authorizationData'][0]['proxyEndpoint']
            username, password = access_token.split(':')

            authorization_data = {
                'username': username,
                'password': password,
                'registry': registry_url
            }

            return authorization_data

        except Exception as err:
            raise err

    def login(self, username, password, registry):
        """Login to AWS ECR registry

        Raises:
            Exception
        """

        try:
            res = self.docker_client.login(
                username,
                password=password,
                registry=registry,
                reauth=True
            )
            LOGGER.debug(res)

        except Exception as err:
            raise err

    def __get_repositories_recursively(self, params, repositories):
        """Recursively get repositories from AWS ECR
        Used self.get_repositories

        Args:
            params (dict): the parameter of ECR.Client.describe_repositories
            repositories (list): list to store gotten repositories
        """

        response = self.ecr_client.describe_repositories(**params)
        repositories += response['repositories']

        try:
            if response['nextToken']:
                params['nextToken'] = response['nextToken']
                self.__get_repositories_recursively(params, repositories)
        except KeyError:
            pass

    def get_repositories(self, params={}):
        """Fetch all repository from AWS ECR

        Args:
            params (dict): parameter of ECR.Client.describe_repositories()

        Returns:
            repositories (list): list includes the return value of
                                 ECR.Client.describe_repositories()
        """

        if not params:
            params = self.params.copy()

        repositories = []
        self.__get_repositories_recursively(params, repositories)
        return repositories

    def get_image_tags(self, params={}):
        """Get image tag

        Args:
            params (dict): parameter of ECR.Client.describe_images()

        Returns:
            image_tags (list): store the return value 'imageTags' of
                               ECR.Client.describe_images()
        """

        if not params:
            params = self.params.copy()

        image_tags = []
        response = self.ecr_client.describe_images(**params)

        for image in response['imageDetails']:
            image_tags += image['imageTags']

        return image_tags

    def tag_exists(self, tag_list, target_tag):
        """Check if docker image includes target tag

        Args:
            tag_list (list): docker image tag list that is the return value
                             of ECR.Client.describe_images()
            target_tag (str): target docker image tag

        Returns:
            boolean
        """
        if target_tag in tag_list:
            return True
        else:
            return False

    def get_image_uris(self):
        """Get docker image URI from AWS ECR

        Returns:
            image_uris (list)
        """

        repositories = self.get_repositories()

        image_uris = [
            repository['repositoryUri'] for repository in repositories
        ]

        return image_uris

    def get_image_uris_filtered_by_tag(self, tag):
        """Get docker image URI from AWS ECR and
        filter by docker image tag

        Args:
            tag (str): docker image tag

        Returns:
            image_uris_with_tag (list): docker image URI list
        """

        repositories = self.get_repositories()
        params = self.params.copy()
        image_uris_with_tag = []

        for repository in repositories:
            params['repositoryName'] = repository['repositoryName']
            params['filter'] = {'tagStatus': 'TAGGED'}

            tag_list = self.get_image_tags(params)

            if self.tag_exists(tag_list, tag):
                image_uri = '{}:{}'.format(repository['repositoryUri'], tag)
                image_uris_with_tag.append(image_uri)

        return image_uris_with_tag
