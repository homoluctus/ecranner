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
    """Pull Docker images in ECR

    Returns:
        pulled_image_list (list)
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
        """Decode ECR access token

        Args:
            token (str): ECR access token (format: base64)

        Raises:
            TypeError: raises when token is not bytes object
        """

        if not isinstance(token, str):
            raise TypeError(
                f'Expected bytes object but current object is {type(token)}')

        bytes_token = base64.b64decode(token)
        return bytes_token.decode('utf-8')

    def authorize(self):
        """Get ECR authorization access token

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
        """Login to ECR registry

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
        """ECRから全リポジトリを再帰的に取得(self.get_repositoriesで使用する)

        Args:
            params: ECR.Client.describe_repositoriesのパラメーター
            repositories: 取得したリポジトリを格納するリスト
        """

        responce = self.ecr_client.describe_repositories(**params)
        repositories += responce['repositories']

        try:
            if responce['nextToken']:
                # nextTokenがセットされていれば再帰する
                params['nextToken'] = responce['nextToken']
                self.__get_repositories_recursively(params, repositories)
        except KeyError:
            pass

    def get_repositories(self, params={}):
        """ECRから全リポジトリを取得

        Args:
            params: ECR.Client.describe_repositoriesのパラメーター

        Returns:
            repositories:
                ECR.Client.describe_repositoriesの返り値に含まれるrepositoriesリスト
        """
        if not params:
            params = self.params.copy()

        repositories = []
        self.__get_repositories_recursively(params, repositories)
        return repositories

    def get_image_tags(self, params={}):
        """イメージのタグを取得

        Args:
            params: ECR.Client.describe_imagesのパラメーター

        Returns:
            image_tags: ECR.Client.describe_imagesの返り値のimageTagsを格納するリスト
        """
        if not params:
            params = self.params.copy()

        image_tags = []
        response = self.ecr_client.describe_images(**params)

        for image in response['imageDetails']:
            image_tags += image['imageTags']

        return image_tags

    def tag_exists(self, tag_list, target_tag):
        """Dockerイメージのタグに特定のタグが存在するかチェック

        Args:
            tag_list: ECR.Client.describe_imagesによって取得したイメージタグリスト
            target_tag: 対象のイメージタグ

        Returns:
            boolean
        """
        if target_tag in tag_list:
            return True
        else:
            return False

    def get_image_uris(self):
        """DockerイメージのURIをECRから取得

        Returns:
            image_uris: イメージのURIを格納したリスト
        """

        repositories = self.get_repositories()

        image_uris = [
            repository['repositoryUri'] for repository in repositories
        ]

        return image_uris

    def get_image_uris_filtered_by_tag(self, tag):
        """イメージタグによってフィルタリングされたイメージURIリストを取得

        Args:
            tag: 対象のイメージタグ

        Returns:
            image_uris_with_tag: 対象のイメージタグをもつイメージのURIを格納するリスト
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
