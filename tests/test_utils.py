import pytest
from ecranner.utils import exception_exists


def test_exception_exists():
    expected_result = 2
    args = [Exception(), 'test', TypeError(), 'hello']
    result = exception_exists(args)
    assert result == expected_result


def test_exception_exists_typeerror():
    with pytest.raises(TypeError):
        exception_exists('ERROR')
