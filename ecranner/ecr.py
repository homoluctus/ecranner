import os
import base64
import boto3

from .log import get_logger
from .docker import DockerImageHandler
from docker.errors import APIError
from .exceptions import (
    DecodeAuthorizationTokenError, AuthorizationError,
    ConfigurationError, PullImageError, LoginRegistryError
)

logger = get_logger()


class ECRHandler(DockerImageHandler):
    """Manipulate AWS ECR"""

    def __init__(self,
                 aws_access_key_id,
                 aws_secret_access_key,
                 region,
                 base_url=None):
        """
        Args:
            aws_access_key_id (str)
            aws_secret_access_key (str)
            region (str)
            profile (str)
        """

        super().__init__(base_url=base_url)

        try:
            self.ecr_client = self.create_ecr_client(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region=region
            )
        except Exception as err:
            self.close()
            raise err

    def create_ecr_client(self,
                          aws_access_key_id=None,
                          aws_secret_access_key=None,
                          region=None,
                          profile=None):
        """Create ECR client

        Args:
            aws_access_key_id (str)
            aws_secret_access_key (str)
            region (str)
            profile (str)

        Returns:
            ECR client

        Raises:
            ConfigurationError
        """

        aws_access_key_id = aws_access_key_id or os.getnev('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = aws_secret_access_key \
            or os.getenv('AWS_SECRET_ACCESS_KEY')
        region = region or os.getenv('AWS_DEFAULT_REGION')

        if aws_access_key_id \
                and aws_secret_access_key \
                and region:
            return boto3.client(
                'ecr',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region
            )
        else:
            raise ConfigurationError('''
                Missing AWS credentials.
                Please configure AWS_ACCESS_KEY_ID,
                AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION
            ''')

    def _decode_token(self, token):
        """Decode AWS ECR access token

        Args:
            token(str): AWS ECR access token(format: base64)

        Returns:
            access_token(tuple): Includes username, password

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

    def authorize(self, account_id):
        """Get AWS ECR authorization access token

        Args:
            account_id(str)

        Returns:
            auth_data(dict): includes username, password and registry URI

        Raises:
            TypeError
            AuthorizationError
            DecodeAuthorizationTokenError
        """

        if not isinstance(account_id, str):
            raise TypeError(
                f'Expected type is str, but the argument is {type(account_id)}'
            )

        try:
            res = self.ecr_client.get_authorization_token(
                registryIds=[account_id]
            )

        except Exception as err:
            raise AuthorizationError(
                f'Failed to get authorization token: {err}'
            )

        logger.info('Got AWS ECR authorization token')

        tmp_auth_data = res['authorizationData'][0]
        username, password = self._decode_token(
            tmp_auth_data['authorizationToken'])
        registry_url = tmp_auth_data['proxyEndpoint']

        auth_data = {
            'username': username,
            'password': password,
            'registry': registry_url
        }

        return auth_data


def pull(images, account_id, region,
         aws_access_key_id, aws_secret_access_key):
    """Pull Docker images from AWS ECR

    Args:
        images (list)
        account_id (str, int)
        region (str)
        aws_access_key_id (str)
        aws_secret_access_key (str)

    Returns:
        pulled_image_list(list): Returns empty list if failed to
            pull docker image or target image does not exist

    Raises:
        TypeError
        PullImageError
    """

    pulled_image_list = []

    if not images:
        return pulled_image_list

    if not isinstance(images, list):
        raise TypeError(
            f'Expected type is list, but the images argument is {type(images)}'
        )

    validated_images = validate_image_name(images, account_id, region)

    try:
        with ECRHandler(aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region=region
                        ) as client:
            auth_data = client.authorize(str(account_id))
            client.login(**auth_data)
            logger.info('Login to AWS ECR Succeeded')

            for image in validated_images:
                pulled_image = client.pull(image,
                                           username=auth_data['username'],
                                           password=auth_data['password'])
                pulled_image_list.append(pulled_image)

        return pulled_image_list

    except (AuthorizationError,
            DecodeAuthorizationTokenError,
            LoginRegistryError,
            APIError
            ) as err:
        raise PullImageError(f'Failed to pull images: {err}')

    except TypeError as err:
        raise err


def validate_image_name(images, account_id, region):
    """Validate image name

    Args:
        images (list): includes image name
        account_id (str)
        region (str)

    Returns:
        validated images list
    """

    validated_images = []
    repository_prefix = f'{account_id}.dkr.ecr.{region}.amazonaws.com'

    for image_name in images:
        if repository_prefix in image_name:
            validated_images.append(image_name)
        else:
            if image_name.startswith('/'):
                validated_image = f'{repository_prefix}{image_name}'
            else:
                validated_image = f'{repository_prefix}/{image_name}'

            validated_images.append(validated_image)

    return validated_images
