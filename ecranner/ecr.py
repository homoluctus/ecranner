import os
import re
import base64
import boto3

from .log import get_logger
from .docker import DockerHandler
from .exceptions import (
    DecodeAuthorizationTokenError, AuthorizationError,
    ExtractAccountIDError, ConfigurationError
)

logger = get_logger()


class ECRHandler(DockerHandler):
    """Manipulate AWS ECR"""

    def __init__(self,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 region=None,
                 profile=None):
        """
        Args:
            aws_access_key_id (str)
            aws_secret_access_key (str)
            region (str)
            profile (str)
        """

        super().__init__()

        try:
            self.ecr_client = self.create_ecr_client(
                aws_access_key_id=None,
                aws_secret_access_key=None,
                region=None,
                profile=None
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

        if profile:
            session = boto3.Session(profile_name=profile)
        elif aws_access_key_id \
                and aws_secret_access_key \
                and region:
            session = boto3.Session(
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

        return session.resource('ecr')

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
            authorization_data(dict): includes username,
                password and registry URI

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

        authorization_data = {}
        for auth_data in res['authorizationData']:
            username, password = self._decode_token(
                auth_data['authorizationToken'])
            registry_url = auth_data['proxyEndpoint']

            account_id = self.extract_account_id(registry_url)

            if not account_id:
                raise ExtractAccountIDError(
                    'Faild to extract AWS account id from registry URL'
                )

            authorization_data[account_id] = {
                'username': username,
                'password': password,
                'registry': registry_url
            }

        return authorization_data

    @classmethod
    def extract_account_id(cls, registry_url):
        """Extract AWS account id from registry_url

        Args:
            registry_url(str)

        Returns:
            account_id(str)
            False
        """

        matched_string = re.search(r'(?<=^https:\/\/)\d+', registry_url)

        if matched_string is None:
            return False

        account_id = matched_string.group(0)
        return account_id


def pull(config):
    """Pull Docker images in AWS ECR

    Args:
        config(dict): includes aws credentials and image names want to pull

    Returns:
        pulled_image_list(list): Returns empty list if failed to
            pull docker image or target image does not exist
    """
    pass
