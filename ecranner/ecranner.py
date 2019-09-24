from pprint import pprint

from . import trivy, slack, utils, ecr
from .docker import DockerImageHandler
from .config import load_dot_env, load_yaml
from .log import get_logger


logger = get_logger()


def run(kwargs):
    """Execute scan and post scan result to slack

    Args:
        kwargs (dict)
    """

    load_dot_env(kwargs['env_file'])
    config = load_yaml(kwargs['file'])
    remove_flag = kwargs['rm']

    pulled_image_list = pull_images(config['aws'], remove_flag)

    if not pulled_image_list:
        logger.info('There are no Docker images to scan')
        logger.info('TERMINATE')
        return

    logger.info('Scanning...')
    payloads = scan_images(pulled_image_list, remove_flag)
    logger.info('Finised Scan')

    if not kwargs['slack']:
        logger.info('TERMINATE')
        return

    logger.info('Posting to Slack...')
    result = slack.post(payloads)
    logger.info('Posted result to Slack')

    if isinstance(result, list):
        failure_num = utils.exception_exists(result)
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


def scan_images(target_image_list, remove_flag=False):
    """Scan target images

    Args:
        target_image_list (list)
        remove_flag (boolean)

    Returns:
        True: if all target image is scanned
    """

    payloads = []

    try:
        for image in target_image_list:
            results = trivy.run(image)

            if results is None:
                continue

            pprint(results, indent=2)
            payloads.append(slack.generate_payload(results, image))

    except Exception as err:
        raise err

    else:
        return payloads

    finally:
        remove_images(target_image_list, remove_flag)
