import os
import sys
import requests
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


def post(payload):
    """Post to Slack

    Args:
        payload (dict)

    Returns:
        boolean

    Raises:
        TypeError: payload is not dict type
        SlackNotificationError: failed to post payload to Slack
        Exception
    """

    try:
        if not isinstance(payload, dict):
            raise TypeError(f'''
                Expected type is "dict",
                but the given argument type is "{type(payload)}"
            ''')

        res = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)

        if res.status_code != 200:
            raise SlackNotificationError(f'''
                Failed to post message to slack
                Response code from slack: {res.status_code}
            ''')

    except Exception as err:
        raise err

    else:
        LOGGER.info('Posted to slack')
        LOGGER.debug(f'Response from slack: {res}')
        return True


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
