_accounts: dict[int, int] = {}


def reset_accounts():

    _accounts.clear()

    _accounts.update(
        {
            1: 100,
            2: 20
        }
    )


def get_balance(
    account_id: int
) -> int:

    return (
        _accounts[
            account_id
        ]
    )


def set_balance(
    account_id: int,
    balance: int
):

    _accounts[
        account_id
    ] = balance