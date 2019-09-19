import json
import pytest
from ecranner.slack import post, generate_payload
from ecranner.exceptions import SlackNotificationError


class TestGeneratePayload:
    def test_success(self):
        with open('tests/assets/test1.json') as f:
            valid_data = json.load(f)

        payload = generate_payload(valid_data)
        assert type(payload) == dict

    def test_type_error(self):
        invalid_data = 'INVALID'

        with pytest.raises(TypeError):
            generate_payload(invalid_data)


class TestSlackNotification:
    def test_post_vuln_data(self):
        """Post Vulnerability information"""

        with open('tests/assets/test1.json') as f:
            vulns = json.load(f)

        payload = generate_payload(vulns)
        result = post(payload)
        assert result is True

    def test_post_vuln_is_null(self):
        """Post data like 'Vulnerabilities': null"""

        with open('tests/assets/test2.json') as f:
            no_vulns = json.load(f)

        payload = generate_payload(no_vulns)
        result = post(payload)
        assert result is True

    def test_post_invalid_payload(self):
        invalid_payload = {'INVALID': 'FAILURE'}

        with pytest.raises(SlackNotificationError):
            post(invalid_payload)

    def test_post_type_error(self):
        type_error_payload = 'INVALID'

        with pytest.raises(TypeError):
            post(type_error_payload)

    def test_mutile_thread_mode(self):
        with open('tests/assets/test1.json') as f:
            data1 = json.load(f)

        with open('tests/assets/test2.json') as f:
            data2 = json.load(f)

        payloads = [
            generate_payload(data1),
            generate_payload(data2)
        ]

        results = post(payloads)

        assert type(results) is list
        assert len(results) == 2
        assert exception_exists(results) is False

    def test_mutile_thread_mode_with_exception(self):
        """Check if the return value of slack.post contains Exception object"""

        with open('tests/assets/test2.json') as f:
            data = json.load(f)

        payloads = [
            generate_payload(data),
            'INVALID'
        ]

        results = post(payloads)

        assert type(results) is list
        assert len(results) == 2
        assert exception_exists(results) == 1


def exception_exists(results):
    exc = list(
        filter(lambda result: isinstance(result, Exception), results)
    )
    num = len(list(exc))
    return num if num >= 1 else False
