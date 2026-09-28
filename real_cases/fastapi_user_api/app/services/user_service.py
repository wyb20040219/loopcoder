from app.repositories.user_repository import (
    count_users,
    save_user
)


def create_user(
    name: str,
    email: str
) -> dict:

    user = {

        "id":
            count_users()
            +
            1,

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