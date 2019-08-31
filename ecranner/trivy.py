import json
import subprocess
from pathlib import Path
from . import log, msg

LOGGER = log.get_logger()


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
                              timeout=300)
        result = json.loads(proc.stdout)
        return result

    except (subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        LOGGER.info(msg.CMD_EXECUTION_ERROR)
        LOGGER.error(err.cmd)
        LOGGER.error(err.stderr)
        return None

    except Exception:
        LOGGER.exception(msg.ERROR)
        return None
