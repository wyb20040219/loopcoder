import pytest

from app.repositories.account_repository import (
    get_balance,
    reset_accounts
)

from app.services.transfer_service import (
    transfer
)


def setup_function():

    reset_accounts()


def test_transfer_success():

    transfer(
        1,
        2,
        30
    )


    assert (
        get_balance(1)
        ==
        70
    )


    assert (
        get_balance(2)
        ==
        50
    )


def test_amount_must_be_positive():

    with pytest.raises(
        ValueError,
        match="amount must be positive"
    ):

        transfer(
            1,
            2,
            0
        )


    assert (
        get_balance(1)
        ==
        100
    )


    assert (
        get_balance(2)
        ==
        20
    )


def test_insufficient_funds():

    with pytest.raises(
        ValueError,
        match="insufficient funds"
    ):

        transfer(
            1,
            2,
            200
        )


    assert (
        get_balance(1)
        ==
        100
    )


    assert (
        get_balance(2)
        ==
        20
    )


def test_same_account_rejected():

    with pytest.raises(
        ValueError,
        match="cannot transfer to same account"
    ):

        transfer(
            1,
            1,
            10
        )


    assert (
        get_balance(1)
        ==
        100
    )