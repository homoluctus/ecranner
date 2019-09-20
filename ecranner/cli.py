import argparse

from .log import get_logger
from .ecranner import run
from .config import YAMLLoader, EnvFileLoader


logger = get_logger()


def parse_args():
    """Generate a parser to analyse the arguments

    Returns:
        vars(args): dictionary stored arguments
    """

    parser = argparse.ArgumentParser(
        prog='ECRanner',
        description='''
            Scan Docker images stored in AWS ECR
            Trivy is used as Vulnerability Scanner
        ''',
        allow_abbrev=False
    )

    parser.add_argument(
        '--rm',
        action='store_true',
        help='remove images after scan with Trivy'
    )

    parser.add_argument(
        '-f',
        '--file',
        default=YAMLLoader.default_config_path(),
        help='filepath to configuration in YAML'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='disable the cache'
    )

    parser.add_argument(
        '--slack',
        action='store_true',
        help='send the scan result to Slack'
    )

    parser.add_argument(
        '--env-file',
        default=EnvFileLoader.default_dot_env_path(),
        help='specify .env file path'
    )

    args = parser.parse_args()

    return vars(args)


def cli():
    args = parse_args()

    try:
        run(args)
    except KeyboardInterrupt:
        logger.warning('Forced terninamtion')
        return 1
