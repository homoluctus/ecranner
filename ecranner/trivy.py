import json
import subprocess
from .log import get_logger
from .exceptions import ConfigurationError

logger = get_logger()


def trivy(image_name, path='trivy',
          options='-q --severity HIGH,CRITICAL'):
    """Scan the vulnerabilities of docker image with Trivy

    Args:
        image_name (str): Docker image name
        path (str): The path of trivy command.
            If path is not specified, we suppose trivy is installed in $PATH.
        options (str): Trivy command options

    Returns:
        result (list): contains dict object stored the scan result
        None: if raise exceptions

    Raises:
        ConfigurationError: if the path argument is invalid
        json.JSONDecodeError
    """

    # `-f json` option is required,
    # so replace empty string if this option is specified
    options = options.replace('-f json', '')
    cmd = f'{path} -f json {options} {image_name}'.split()

    try:
        proc = subprocess.run(cmd, check=True,
                              capture_output=True,
                              timeout=600)

    except FileNotFoundError:
        raise ConfigurationError(
            f'{repr(path)} is invalid as trivy command path. '
            'Please set the correct path that trivy command is stored')

    except (subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        logger.error(
            f'Failed to scan {image_name} with Trivy. '
            f'Execution command: {" ".join(err.cmd)}')
        return None

    except Exception as err:
        raise err

    try:
        return json.loads(proc.stdout)

    except json.JSONDecodeError as err:
        raise err
