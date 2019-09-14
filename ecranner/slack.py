import os
import sys
import requests
import concurrent.futures as confu

from . import log, msg
from .exceptions import SlackNotificationError


LOGGER = log.get_logger()

try:
    SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
except KeyError:
    LOGGER.exception(f'"SLACK_WEBHOOK"{msg.ENV_CONFIGURE}')
    sys.exit(1)

SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
SLACK_ICON = os.getenv('SLACK_ICON', ':trivy:')


def post(payloads, max_workers=None, timeout=60):
    """Post to Slack

    Args:
        payloads (dict, list): Be thread mode when type(payloads) is list
        max_workers (int): The number of thread
        timeout (int): Time (seconds) to wait for the response

    Returns:
        True or list contains True or Exceptions
        Retuns list when runs with multi thread mode

    Raises:
        TypeError
        SlackNotificationError
        Exception
    """

    if isinstance(payloads, dict):
        return __post_single_payload(payloads, timeout)

    elif isinstance(payloads, list):
        if len(payloads) == 1:
            return __post_single_payload(payloads[0], timeout)
        else:
            return __post_with_thread_mode(payloads, max_workers, timeout)

    else:
        raise TypeError(f'''
            Expected type is "dict" or "list",
            but the given argument type is "{type(payloads)}"
        ''')


def __post_single_payload(payload, timeout):
    """This method is executed in internal post method

    Args:
        payload (dict)
        timeout (int): Time (seconds) to wait for the response

    Returns:
        boolean

    Raises:
        SlackNotificationError: failed to post payload to Slack
        Exception
    """

    try:
        res = requests.post(SLACK_WEBHOOK, json=payload, timeout=timeout)

        if res.status_code != 200:
            raise SlackNotificationError(f'''
                Failed to post message to slack
                Response code from slack: {res.status_code}
            ''')

    except Exception as err:
        raise err

    else:
        LOGGER.debug(f'Response from slack: {res}')
        return True


def __post_with_thread_mode(payloads, max_workers, timeout):
    """Post to Slack with thread mode

    Args:
        payloads (list)
        max_workers (int): The number of thread
        timeout (int): Time (seconds) to wait for the response

    Returns:
        results: Contains True or Exceptions
    """

    results = []

    with confu.ThreadPoolExecutor(max_workers=max_workers) as thread:
        future_to_response = {
            thread.submit(
                __post_single_payload,
                payload,
                timeout
            ): payload for payload in payloads
        }

        for future in confu.as_completed(future_to_response):
            try:
                results.append(future.result())
            except Exception as err:
                results.append(err)

        return results


def generate_payload(results, image_name=''):
    """Generate payload for Slack

    Args:
        results (list): The result of scan using trivy
        image_name (str): Used as payload text message

    Returns:
        payload (dict)

    Raises:
        TypeError
    """

    if not isinstance(results, list):
        raise TypeError(f'''
                Expected type is "list",
                but the given argument type is "{type(results)}"
        ''')

    if not isinstance(image_name, str):
        raise TypeError(f'''
                Expected type is "str",
                but the given argument type is "{type(image_name)}"
        ''')

    attachments = []
    payload = {'username': 'Trivy'}
    color = {'vuln_found': '#cb2431', 'vuln_not_found': '#2cbe4e'}

    if image_name != '':
        payload['text'] = f'*{image_name.split("/")[0]}*'

    if SLACK_CHANNEL:
        payload['channel'] = SLACK_CHANNEL

    if SLACK_ICON.startswith('http'):
        payload['icon_url'] = SLACK_ICON
    else:
        payload['icon_emoji'] = SLACK_ICON

    for item in results:
        target_name = item.get('Target')
        suffix_target_name = target_name.split('/')[-1]

        if image_name != '' and image_name not in target_name:
            # for application dependencies tool
            title = f'*{image_name.split("/")[-1]} - {suffix_target_name}*'
        else:
            title = f'*{suffix_target_name}*'

        tmp_attachment = {
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': title
                    }
                }
            ]
        }

        if item['Vulnerabilities'] is None:
            contents = {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'Not Found Vulnerabilities'
                }
            }
            tmp_attachment['color'] = color['vuln_not_found']
            tmp_attachment['blocks'].append(contents)

        else:
            counter = 1
            tmp_attachment['color'] = color['vuln_found']

            for vuln in item['Vulnerabilities']:
                contents = {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '*{}. {}*\n{}'.format(
                            counter,
                            vuln['PkgName'],
                            vuln['Description'])
                    },
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': '*Vulnerability ID*\n{}'.format(
                                vuln['VulnerabilityID'])
                        },
                        {
                            'type': 'mrkdwn',
                            'text': '*Severity*\n{}'.format(vuln['Severity'])
                        }
                    ]
                }

                references = ''
                for ref in vuln['References']:
                    references += f'- {ref}\n'

                reference_section = {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f'*Reference*\n{references}'
                    }
                }

                tmp_attachment['blocks'].append(contents)
                tmp_attachment['blocks'].append(reference_section)
                counter += 1

        attachments.append(tmp_attachment)

    payload['attachments'] = attachments

    return payload
