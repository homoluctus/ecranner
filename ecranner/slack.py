import os
import sys
import requests
from . import log, msg


LOGGER = log.get_logger()

try:
    SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK']
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
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

    if SLACK_CHANNEL:
        payload['channel'] = SLACK_CHANNEL

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

    attachments = []

    for item in result:
        tmp_attachment = {
            'color': '#cb2431',
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
            tmp_attachment['blocks'].append(contents)

        else:
            counter = 1

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

    payload = {'attachments': attachments}
    return payload
