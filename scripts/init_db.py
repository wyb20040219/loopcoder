from db.base import Base

from db.session import (
    engine,
)

import db.models  # noqa: F401


def main():

    print(
        "Creating database tables..."
    )

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database tables created."
    )


if __name__ == "__main__":

    main()