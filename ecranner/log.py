import os
import logging


def get_logger():
    """Loggerを作成する

    Returns:
        logger: logging.Loggerクラスのインスタンス
    """

    log_format = \
        '[%(asctime)s] %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    logging.basicConfig(
        format=log_format,
        level=os.getenv('LOG_LEVEL', default='INFO')
    )
    logger = logging.getLogger(__name__)
    return logger
