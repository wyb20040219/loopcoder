_users: list[dict] = []


def clear_users():

    _users.clear()


def count_users() -> int:

    return len(
        _users
    )


def find_by_email(
    email: str
) -> dict | None:

    for user in _users:

        if (
            user[
                "email"
            ]
            ==
            email
        ):

            return dict(
                user
            )


    return None


def save_user(
    user: dict
) -> dict:

    saved = dict(
        user
    )


    _users.append(
        saved
    )


    return dict(
        saved
    )