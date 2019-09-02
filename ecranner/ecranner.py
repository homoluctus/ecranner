from . import trivy, ecr, msg, log, slack


LOGGER = log.get_logger()


def main():
    """Execute scan and post scan result to slack"""

    LOGGER.info(msg.START_PROCESS)

    image_list = ecr.pull_images()

    if not image_list:
        LOGGER.info('There are no Docker images to scan')
        LOGGER.info(msg.FINISH_PROCESS)
        return

    LOGGER.info('Scanning Docker images')
    for image in image_list:
        result = trivy.run(image)

        if result is None:
            continue

        slack.post(result)

    LOGGER.info(msg.FINISH_PROCESS)
