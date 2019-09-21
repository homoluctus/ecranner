from . import trivy, ecr, msg, log, slack, utils


LOGGER = log.get_logger()


def run(kwargs={}):
    """Execute scan and post scan result to slack"""

    LOGGER.info(msg.START_PROCESS)

    image_list = ecr.pull_images()

    if not image_list:
        LOGGER.info('There are no Docker images to scan')
        LOGGER.info(msg.FINISH_PROCESS)
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

    LOGGER.info(msg.FINISH_PROCESS)
