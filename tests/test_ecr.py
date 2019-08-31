import pytest
from ecranner.ecr import (
    execute_cmd, ECRHandler
)
from subprocess import (
    CompletedProcess, CalledProcessError
)


class TestExecuteCmd:
    def test_success(self):
        cmd = ['ls']
        result = execute_cmd(cmd)
        assert isinstance(result, CompletedProcess) is True
        assert result.returncode == 0

    def test_invalid_type_cmd(self):
        invalid_cmd = {1: 'ls'}
        with pytest.raises(TypeError):
            execute_cmd(invalid_cmd)

    def test_failure(self):
        invalid_cmd = ['ls', '/nonexistance']
        with pytest.raises(CalledProcessError):
            execute_cmd(invalid_cmd)


class TestECRHandler:
    def test_pull(self):
        image_name = 'alpine:latest'
        result = ECRHandler.pull(image_name)
        assert isinstance(result, CompletedProcess) is True
        assert result.returncode == 0

    def test_pull_nonexistant_image(self):
        image_name = 'nonexistant_image'
        with pytest.raises(CalledProcessError):
            ECRHandler.pull(image_name)

    def test_ecr_login(self):
        result = ECRHandler.login()
        assert isinstance(result, CompletedProcess) is True
        assert result.returncode == 0
