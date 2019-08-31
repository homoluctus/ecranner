import json
from ecranner.slack import post


class TestSlackNotification:
    def test_post_vuln_data(self):
        """Post Vulnerability information"""

        with open('./tests/test1.json') as f:
            data = json.load(f)

        result = post(data)
        assert result is True

    def test_post_vuln_is_null(self):
        """Post data like 'Vulnerabilities': null"""

        with open('./tests/test2.json') as f:
            data = json.load(f)

        result = post(data)
        assert result is True

    def test_post_invalid_payload(self):
        invalid_payload = 'INVALID'
        result = post(invalid_payload)
        assert result is False
