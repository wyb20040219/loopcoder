import pytest

from app.repositories.user_repository import (
    clear_users
)

from app.services.user_service import (
    create_user
)

from app.utils.email_utils import (
    normalize_email
)


def setup_function():

    clear_users()


def test_normalize_email():

    assert (
        normalize_email(
            "  Alice@Example.COM  "
        )
        ==
        "alice@example.com"
    )


def test_create_user_stores_normalized_email():

    user = (
        create_user(

            name=
                "Alice",

            email=
                "  Alice@Example.COM  "
        )
    )


    assert (
        user["email"]
        ==
        "alice@example.com"
    )


def test_duplicate_email_is_case_insensitive():

    create_user(

        name=
            "Alice",

        email=
            "Alice@Example.com"
    )


    with pytest.raises(
        ValueError,
        match="email already exists"
    ):

        create_user(

            name=
                "Another Alice",

            email=
                "alice@example.COM"
        )