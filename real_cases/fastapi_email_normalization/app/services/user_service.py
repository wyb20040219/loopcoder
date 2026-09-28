from app.repositories.user_repository import (
    find_by_email,
    save_user
)


def create_user(
    name: str,
    email: str
) -> dict:

    if (
        find_by_email(
            email
        )
        is not None
    ):

        raise ValueError(
            "email already exists"
        )


    user = {

        "name":
            name,

        "email":
            email
    }


    return (
        save_user(
            user
        )
    )