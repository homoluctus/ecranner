import base64
import boto3
import docker
from . import log, msg
from .docker import DockerHandler
from .exceptions import (
    ImageMismatchedError, LoginRegistryError,
    DecodeAuthorizationTokenError,
)
from .config import EnvFileLoader

logger = log.get_logger()


class ECRHandler(DockerHandler):
    def __init__(self):
        super().__init__()
        self.ecr_client = boto3.client('ecr')
        self.params = {'registryId': AWS_ACCOUNT_ID}

    def pull(self, image_name, username=None, password=None):
        """Pull Docker image

        Args:
            image_name (str): Docker image name (includes tag)
            username (str)
            password (str)

        Returns:
            image_name (str): Docker image name
        """

        try:
            # pre check if specified docker image is already pulled
            self.docker_client.images.get(image_name)
            logger.info(f'{image_name} already exists')
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
            logger.info(f'Pulled {image_name}')

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

        Returns:
            access_token (tuple): Includes username, password

        Raises:
            TypeError: raises when token is not bytes object
            DecodeAuthorizationTokenError
        """

        if not isinstance(token, str):
            raise TypeError(
                f'Expected bytes object but current object is {type(token)}')

        bytes_token = base64.b64decode(token)
        decoded_token = bytes_token.decode('utf-8')

        if not isinstance(decoded_token, str):
            raise DecodeAuthorizationTokenError(
                'Failed to decode authorization token')

        access_token = tuple(decoded_token.split(':'))
        return access_token

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

            username, password = self.__decode_token(
                res['authorizationData'][0]['authorizationToken'])
            registry_url = res['authorizationData'][0]['proxyEndpoint']

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
            LoginRegistryError
        """

        try:
            res = self.docker_client.login(
                username,
                password=password,
                registry=registry,
                reauth=True
            )

        except Exception as err:
            raise LoginRegistryError(f'Failed to Login to ECR: {err}')

        else:
            logger.debug(res)

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
            params (dict):
                parameter of ECR.Client.describe_repositories()

        Returns:
            repositories (list):
                list includes the return value of
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
            image_tags (list):
                store the return value 'imageTags' of
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
            tag_list (list):
                Docker image tag list that is the return value
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


def pull(config):
    """Pull Docker images in AWS ECR

    Args:
        config (dict): includes aws credentials and image names want to pull

    Returns:
        pulled_image_list (list):
            Returns empty list if failed to pull docker image
            or target image does not exist
    """

    pulled_image_list = []

    try:
        with ECRHandler() as ecr:
            auth_data = ecr.authorize()
            ecr.login(**auth_data)
            logger.info(f'ECRへ{msg.LOGIN_SUCCESS}')
            image_list = ecr.get_image_uris_filtered_by_tag(IMAGE_TAG)
            for image_name in image_list:
                ecr.pull(
                    image_name,
                    auth_data['username'],
                    auth_data['password']
                )
                pulled_image_list.append(image_name)

    except Exception as err:
        logger.error(err, exc_info=True)

    return pulled_image_list


def set_credentials_as_env(config, override=False):
    """Set aws credentials as system environment variable

    Args:
        config (dict)
        override (boolean)

    Returns:
        boolean

    Raises:
        TypeError
    """

    credentials = extract_credentials(config)
    return EnvFileLoader.set_env_from_dict(credentials, override)


def extract_credentials(config):
    """Extract aws credentials from config

    Args:
        config (dict)

    Returns:
        aws_credentials (dict)
    """

    params = [
        'aws_access_key_id',
        'aws_secret_access_key',
        'aws_default_region'
    ]

    aws_credentials = {
        str(key).upper(): str(config[key])
        for key in config.keys() if key in params
    }

    return aws_credentials
