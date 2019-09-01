import sys
import os
import boto3
import docker
import subprocess
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


def run():
    """ECRからDockerイメージURIを取得してPullする

    Returns:
        PullされたDockerイメージ名のリスト
    """

    image_name_list = get_images(IMAGE_TAG)
    return pull_images(image_name_list)


def get_images(tag='latest'):
    """ECRからDockerイメージURIを取得

    Returns:
        image_uris: タグ付のイメージURIのリスト
    """

    ecr = ECRHandler()
    image_uris = ecr.get_image_uris_filtered_by_tag(tag)
    return image_uris


def pull_images(image_name_list):
    """ECRからDockerイメージをプル

    Args:
        image_name_list: 取得対象のイメージ名のリスト(空であればECRにある全てのイメージを取得)

    Returns:
        pulled_image_list: 正常にプルしたDockerイメージ名が格納されたリスト
        None: ログイン失敗
    """

    try:
        ECRHandler.login(AWS_DEFAULT_REGION)

    except subprocess.CalledProcessError as err:
        LOGGER.error(err.cmd)
        LOGGER.error(err.stderr)
        return None

    except Exception:
        LOGGER.exception(msg.ERROR)
        return None

    else:
        LOGGER.info(msg.LOGIN_SUCCESS)

    pulled_image_list = []

    for image_name in image_name_list:
        try:
            client = ECRHandler(image_name)
            client.pull(image_name)

        except Exception as err:
            LOGGER.error(err, exc_info=True)

        else:
            LOGGER.info(f'Pulled {image_name}')
            pulled_image_list.append(image_name)

        finally:
            # close docker session
            client.close()

    return pulled_image_list


def execute_cmd(cmd):
    """コマンドを実行

    Args:
        cmd: コマンドのリスト ex)['ls', '-l']

    Returns:
        proc: subprocess.CompletedProcess(コマンドが完了した場合)
    """

    try:
        proc = subprocess.run(
            cmd, capture_output=True, check=True,
            timeout=300, encoding='utf-8')

        LOGGER.debug(proc.stdout)

        return proc

    except Exception as err:
        raise err


class ECRHandler:
    def __init__(self):
        self.ecr_client = boto3.client('ecr')
        self.params = {'registryId': AWS_ACCOUNT_ID}
        self.docker_client = docker.DockerClient(
            base_url='unix:///var/run/docker.sock',
            version='auto',
            timeout=60,
        )

    def pull(self, image_name, username=None, password=None):
        """Pull Docker image

        Args:
            image_name: Docker image name

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

        try:
            image = self.docker_client.images.pull(
                image_name,
                auth_config={
                    'username': username,
                    'password': password
                }
            )

            pulled_image_name = image.tags[0]

            if pulled_image_name != image_name:
                raise ImageMismatchedError(f'''
                    Pulled image: {pulled_image_name}
                    Expected image: {image_name}
                ''')

            return pulled_image_name

        except (docker.errors.APIError,
                ImageMismatchedError) as err:
            raise err

    @classmethod
    def login(cls, region):
        """Login to ECR

        Args:
            region (str)
        """

        ecr_login_cmd = [
            'aws', 'ecr', 'get-login',
            '--region', region, '--no-include-email'
        ]
        result = execute_cmd(ecr_login_cmd)
        stdout = result.stdout.rstrip('\n')
        docker_login_cmd = stdout.split(' ')
        return execute_cmd(docker_login_cmd)

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
            params = self.params

        image_tags = []
        response = self.ecr_client.describe_images(**params)

        for image in response['imageDetails']:
            image_tags += image['imageTags']

        return image_tags

    def exist_tag(self, tag_list, target_tag):
        """Dockerイメージのタグに特定のタグが存在するかチェック

        Args:
            tag_list: ECR.Client.describe_imagesによって取得したイメージタグリスト
            target_tag: 対象のイメージタグ

        Returns:
            boolean: 引数のtarget_tagがtag_listに存在すればTrue
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

            if self.exist_tag(tag_list, tag):
                image_uri = '{}:{}'.format(repository['repositoryUri'], tag)
                image_uris_with_tag.append(image_uri)

        return image_uris_with_tag
