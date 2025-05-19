import boa
import pytest


@pytest.fixture
def simple_account():
    return boa.load("SimpleAccount.vy")


def test_set_foo(simple_account):
    simple_account.validateUserOp()
    assert 1 == 2
