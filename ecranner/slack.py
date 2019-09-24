import requests
import concurrent.futures as confu

from .log import get_logger
from .exceptions import SlackNotificationError


logger = get_logger()


def post(url, payloads, max_workers=None, timeout=60):
    """Post to Slack

    Args:
        url (str): slack incoming webhook url
        payloads (dict, list): Be thread mode when type(payloads) is list
        max_workers (int): The number of thread
        timeout (int): Time (seconds) to wait for the response

    Returns:
        True
        List: Contains True or Exceptions if runs with multi thread mode

    Raises:
        TypeError
        SlackNotificationError
    """

    if isinstance(payloads, dict):
        return __post_single_payload(url, payloads, timeout)

    elif isinstance(payloads, list):
        if len(payloads) == 1:
            return __post_single_payload(url, payloads[0], timeout)
        else:
            # runs with multi thread mode
            return __post_with_thread_mode(url, payloads, max_workers, timeout)

    else:
        raise TypeError(f'Expected type is "dict" or "list", '
                        'but the given argument type is "{type(payloads)}"')


def __post_single_payload(url, payload, timeout):
    """This method is executed in internal post method

    Args:
        url (str): slack incoming webhook url
        payload (dict)
        timeout (int): Time (seconds) to wait for the response

    Returns:
        boolean

    Raises:
        SlackNotificationError: failed to post payload to Slack
    """

    try:
        res = requests.post(url, json=payload, timeout=timeout)

        if res.status_code != 200:
            raise SlackNotificationError(f'''
                Failed to post message to slack
                Response code from slack: {res.status_code}
            ''')

    except Exception as err:
        raise SlackNotificationError(f'Could not send message to Slack: {err}')

    else:
        logger.debug(f'Response from slack: {res}')
        return True


def __post_with_thread_mode(url, payloads, max_workers, timeout):
    """Post to Slack with thread mode

    Args:
        url (str): slack incoming webhook url
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
                url,
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


def generate_payload(results, image_name='', channel='', icon=''):
    """Generate payload for Slack

    Args:
        results (list): The result of scan using trivy
        image_name (str): Used as payload text message
        channel (str): the channel to send message
        icon (str): slack icon

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

    if channel:
        payload['channel'] = channel

    if icon.startswith('http'):
        payload['icon_url'] = icon
    else:
        payload['icon_emoji'] = icon

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
