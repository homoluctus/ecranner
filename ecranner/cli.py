import argparse


def parse_args():
    """Generate a parser to analyse the arguments

    Returns:
        args
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
        default='ecranner.yml',
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

    args = parser.parse_args()

    return args
