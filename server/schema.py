import re
from typing import ClassVar

from pydantic import BaseModel, ValidationError, field_validator

from server.exceptions import HttpError


class BaseUser(BaseModel):
    username: str
    password: str

    password_pattern: ClassVar = re.compile(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).*$")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        result = cls.password_pattern.fullmatch(value)
        if result:
            return value
        raise ValueError(
            "The password too simple. It must contain " "numbers, uppercase and lowercase letters."
        )


class CreateUser(BaseUser):
    pass


class UpdateUser(BaseUser):
    username: str | None = None
    password: str | None = None


class BaseAdvertisement(BaseModel):
    title: str
    text: str


class CreateAdvertisement(BaseAdvertisement):
    pass


class UpdateAdvertisement(BaseAdvertisement):
    title: str | None = None
    text: str | None = None


def validate(
    schema: CreateUser | UpdateUser | CreateAdvertisement | UpdateAdvertisement,
    input_data: dict,
):
    try:
        data = schema(**input_data)
        return data.model_dump(exclude_unset=True)
    except ValidationError as error:
        errors = error.errors()
        for error in errors:
            error.pop("ctx", None)
        raise HttpError(400, errors)
