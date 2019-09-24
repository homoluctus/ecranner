import argparse

from . import __version__
from .log import get_logger
from .ecranner import run
from .config import YAMLLoader


logger = get_logger()


def parse_args():
    """Generate a parser to analyse the arguments

    Returns:
        vars(args): dictionary stored arguments
    """

    parser = argparse.ArgumentParser(
        prog='ECRanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
            Scan Docker images stored in AWS ECR.
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
        help='''
            specify .env file path
            (automatically load .env file
            if this file is found in current directory)
        '''
    )

    parser.add_argument(
        '-q',
        '--quiet',
        action='store_false',
        help='suppress logging message'
    )

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=f'version: {__version__}',
        help='show version'
    )

    args = parser.parse_args()

    return vars(args)


def main():
    args = parse_args()
    logger.propagate = args['quiet']

    try:
        run(args)

    except KeyboardInterrupt:
        logger.warning('Forced terninamtion')
        return False

    except Exception as err:
        logger.error(err)
        return False
