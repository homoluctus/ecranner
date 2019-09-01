import os
import sys
import requests
from . import log, msg


LOGGER = log.get_logger()

try:
    SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
    SLACK_ICON = os.getenv('SLACK_ICON', ':trivy:')
except KeyError:
    LOGGER.exception(f'"SLACK_WEBHOOK"{msg.ENV_CONFIGURE}')
    sys.exit(1)


def post(result):
    """Post to Slack

    Args:
        result: scann result

    Returns:
        boolean
    """

    if not isinstance(result, list):
        return False

    payload = generate_payload(result)
    LOGGER.debug(payload)

    try:
        res = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)

        if res.status_code != 200:
            raise Exception(f'''
                Failed to post message to slack
                Response from slack: {res}
            ''')

        LOGGER.info('Posted to slack')
        LOGGER.debug(f'Response from slack: {res}')
        return True

    except Exception as err:
        LOGGER.error(err, exc_info=True)
        return False


def generate_payload(result):
    """Generate payload for slack

    Args:
        result (dict): the result of scan using trivy

    Returns:
        payload (dict)
    """

    payload = {'username': 'Trivy'}
    attachments = []
    color = {'vuln_found': '#cb2431', 'vuln_not_found': '#2cbe4e'}

    if SLACK_CHANNEL:
        payload['channel'] = SLACK_CHANNEL

    if SLACK_ICON.startswith('http'):
        payload['icon_url'] = SLACK_ICON
    else:
        payload['icon_emoji'] = SLACK_ICON

    for item in result:
        tmp_attachment = {
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '*{}*'.format(item['Target'])
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

                reference_field = {
                    'type': 'mrkdwn',
                    'text': '*Reference*\n{}'.format(references)
                }

                contents['fields'].append(reference_field)
                tmp_attachment['blocks'].append(
                    contents)
                counter += 1

        attachments.append(tmp_attachment)

    payload['attachments'] = attachments

    return payload
