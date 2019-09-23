from pprint import pprint

from . import trivy, slack, utils, ecr
from .docker import remove_images
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

    pulled_image_list = []
    for aws_config in config['aws'].values():
        tmp = ecr.pull(**aws_config)

        if isinstance(tmp, str):
            pulled_image_list.append(tmp)
        elif isinstance(tmp, list):
            pulled_image_list.extend(tmp)

    if not pulled_image_list:
        logger.info('There are no Docker images to scan')
        logger.info('TERMINATE')
        return

    payloads = []

    logger.info('Scanning...')

    for image in pulled_image_list:
        results = trivy.run(image)

        if results is None:
            continue

        pprint(results, indent=2)
        payloads.append(slack.generate_payload(results, image))

    logger.info('Finised Scan')

    if kwargs['rm']:
        remove_images(pulled_image_list)

    if not kwargs['slack']:
        logger.info('TERMINATE')
        return

    logger.info('Posting to Slack...')
    result = slack.post(payloads)
    logger.info('Posted result to Slack')

    if isinstance(result, list):
        failure_num = utils.exception_exists(result)
        suffix = 'scan result messages'
        logger.info(f'''
            SUCCESS: {len(result) - failure_num} {suffix}
            FAILURE: {failure_num} {suffix}
        ''')

    logger.info('TERMINATE')
    return
