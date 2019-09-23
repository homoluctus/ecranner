from . import trivy, ecr, slack, utils
from .log import get_logger


LOGGER = get_logger()


def run(aws_config, trivy_options):
    """Execute scan and post scan result to slack

    Args:
        aws_config (dict)
        trivy_options (dict)
    """

    LOGGER.info('START ECRanner')

    image_list = ecr.pull(**aws_config)

    if not image_list:
        LOGGER.info('There are no Docker images to scan')
        LOGGER.info('TERMINATE')
        return

    payloads = []

    LOGGER.info('Scanning...')

    for image in image_list:
        results = trivy.run(image)

        if results is None:
            continue

        payloads.append(slack.generate_payload(results, image))

    LOGGER.info('Finised Scan')
    LOGGER.info('Posting to Slack...')

    result = slack.post(payloads)

    LOGGER.info('Posted result to Slack')

    if isinstance(result, list):
        failure_num = utils.exception_exists(result)
        suffix = 'scan result messages'
        LOGGER.info(f'''
            SUCCESS: {len(result) - failure_num} {suffix}
            FAILURE: {failure_num} {suffix}
        ''')

    LOGGER.info('TERMINATE')
    return
