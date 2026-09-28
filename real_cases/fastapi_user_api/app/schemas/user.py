from pydantic import (
    BaseModel,
    EmailStr
)


class UserCreate(
    BaseModel
):

    name: str

    email: EmailStr


class UserOut(
    BaseModel
):

    id: int

    name: str

    email: EmailStr