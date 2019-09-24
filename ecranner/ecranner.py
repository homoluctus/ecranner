import os
from pprint import pprint

from . import slack, ecr
from .utils import exception_exists
from .trivy import trivy
from .docker import DockerImageHandler
from .config import load_dot_env, load_yaml
from .log import get_logger
from .exceptions import ConfigurationError, SlackNotificationError


logger = get_logger()


def run(kwargs):
    """Execute scan and post scan result to slack

    Args:
        kwargs (dict)
    """

    load_dot_env(kwargs['env_file'])
    config = load_yaml(kwargs['file'])
    remove_flag = kwargs['rm']

    try:
        aws_config = config['aws']
    except KeyError:
        raise ConfigurationError('Missing AWS configurations')

    pulled_image_list = pull_images(aws_config, remove_flag)

    if not pulled_image_list:
        logger.info('There are no Docker images to scan')
        logger.info('TERMINATE')
        return

    logger.info('Scanning...')
    trivy_config = config.get('trivy', {})
    scan_results = scan_images(pulled_image_list,
                               remove_flag=remove_flag,
                               trivy_config=trivy_config)
    logger.info('Finised Scan')

    if not kwargs['slack']:
        logger.info('TERMINATE')
        return

    slack_url = os.getenv('SLACK_WEBHOOK')

    if slack_url is None:
        raise SlackNotificationError(
            'Could not send the scan result to Slack '
            'because "SLACK_WEBHOOK" environment variable is not set. '
            'Please configure as environment variable.')

    slack_channel = os.getenv('SLACK_CHANNEL')
    slack_icon = os.getenv('SLACK_ICON', ':trivy:')

    payloads = [slack.generate_payload(
                result, image_name, slack_channel, slack_icon)
                for image_name, result in scan_results.items()]

    logger.info('Posting to Slack...')
    result = slack.post(slack_url, payloads)
    logger.info('Posted result to Slack')

    if isinstance(result, list):
        failure_num = exception_exists(result)
        suffix = 'scan result messages'
        logger.info(f'''SUCCESS: {len(result) - failure_num} {suffix}
                    FAILURE: {failure_num} {suffix}''')

    logger.info('TERMINATE')
    return


def pull_images(aws_provider, remove_flag=False):
    """Pull images from AWS ECR

    Args:
        aws_provider (dict)
        remove_flag (boolean)

    Returns:
        pulled_image_list (list)
    """

    pulled_image_list = []

    try:
        for aws_config in aws_provider.values():
            tmp = ecr.pull(**aws_config)

            if isinstance(tmp, str):
                pulled_image_list.append(tmp)
            elif isinstance(tmp, list):
                pulled_image_list.extend(tmp)

    except Exception as err:
        remove_images(pulled_image_list, remove_flag)
        raise err

    else:
        return pulled_image_list


def remove_images(target_image_list, remove_flag=False):
    """Remove pulled docker images

    Args:
        target_image_list (list)
        remove_flag (boolean)

    Returns:
        boolean
    """

    if remove_flag:
        with DockerImageHandler() as client:
            result = client.remove_images(target_image_list)

        if isinstance(result, list):
            logger.warning(f'Failed to remove all images: {result}')
            return False

        elif result:
            logger.info('Remove all target images')

    return True


def scan_images(target_image_list, remove_flag=False, trivy_config={}):
    """Scan target images

    Args:
        target_image_list (list)
        remove_flag (boolean)
        trivy_config (dict): includes trivy command path and options

    Returns:
        results (dict): key is image name and value is scan result
    """

    results = {}

    try:
        for image in target_image_list:
            scan_result = trivy(image, **trivy_config)

            if scan_result is None:
                continue

            pprint(scan_result, indent=2)
            results[image] = scan_result

    except Exception as err:
        raise err

    else:
        return results

    finally:
        remove_images(target_image_list, remove_flag)
