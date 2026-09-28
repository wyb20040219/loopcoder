import pytest

from app.repositories.user_repository import (
    clear_users,
    count_users
)

from app.services.user_service import (
    create_user
)


def setup_function():

    clear_users()


def test_create_user():

    user = create_user(

        name=
            "Alice",

        email=
            "alice@example.com"
    )


    assert (
        user[
            "id"
        ]
        ==
        1
    )


    assert (
        user[
            "email"
        ]
        ==
        "alice@example.com"
    )


def test_duplicate_email_rejected():

    create_user(

        name=
            "Alice",

        email=
            "alice@example.com"
    )


    with pytest.raises(
        ValueError,
        match="email already exists"
    ):

        create_user(

            name=
                "Another Alice",

            email=
                "alice@example.com"
        )


def test_duplicate_email_does_not_create_second_user():

    create_user(

        name=
            "Alice",

        email=
            "alice@example.com"
    )


    try:

        create_user(

            name=
                "Another Alice",

            email=
                "alice@example.com"
        )


    except ValueError:

        pass


    assert (
        count_users()
        ==
        1
    )