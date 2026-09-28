from app.repositories.account_repository import (
    get_balance,
    set_balance
)


def transfer(
    from_account_id: int,
    to_account_id: int,
    amount: int
):

    from_balance = (
        get_balance(
            from_account_id
        )
    )


    to_balance = (
        get_balance(
            to_account_id
        )
    )


    set_balance(

        from_account_id,

        from_balance
        -
        amount
    )


    set_balance(

        to_account_id,

        to_balance
        +
        amount
    )