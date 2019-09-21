import json
import subprocess
from .log import get_logger

LOGGER = get_logger()


def run(image_name):
    """trivyコマンドによって脆弱性スキャンを実施

    Args:
        image_name: Docker image name

    Returns:
        result: スキャン結果
        None: エラーが発生した場合
    """

    cmd = [
        'trivy', '--severity', 'HIGH,CRITICAL',
        '-f', 'json', '-q', image_name
    ]

    try:
        proc = subprocess.run(cmd, check=True,
                              capture_output=True,
                              timeout=600)
        result = json.loads(proc.stdout)
        return result

    except (subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        LOGGER.info('Failed to execute trivy command')
        LOGGER.error(err.cmd)
        LOGGER.error(err.stderr)
        return None

    except Exception as err:
        LOGGER.error(err)
        return None
