import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import Request, request

from server.config import SECRET_KEY
from server.exceptions import HttpError
from server.models import User


def encode_token(user: User) -> dict:
    """Функция формирования токена авторизации.

    В качестве шифруемых в токен данных выступает словарь с идентификатором пользователя,
    Возвращает словарь с токеном, действительным в течении одного часа.
    """
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(minutes=60)
    auth_token: str = jwt.encode(
        {"id": user.id, "exp": expiration_time},
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"auth_token": auth_token}


def _decode_token(token: str) -> dict:
    """Функция проверки подлинности предоставленного токена.

    Возвращает зашифрованные данные - словарь с идентификатором пользователя.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        raise HttpError(401, "The provided authorization token is invalid")


def _check_permissions_for_advertisement(is_owner: bool, kwargs: dict) -> None:
    if request.is_authenticated:
        if is_owner and kwargs:
            for advertisement in request.user.advertisements:
                if advertisement.id == kwargs["id"]:
                    return
            raise HttpError(403, "You can only make changes to your own advertisements")
    else:
        raise HttpError(401, "Authorization credentials were not provided")


def _check_permissions_for_user(is_owner: bool, kwargs: dict) -> None:
    if request.is_authenticated:
        if is_owner and kwargs:
            if request.user.id == kwargs["id"]:
                return
            raise HttpError(403, "You can only make changes to your own profile")
    else:
        raise HttpError(401, "Authorization credentials were not provided")


def check_authentication(request: Request):
    """Функция аутентификации пользователя.

    Результатом выполнения является добавление в объект запроса следующих атрибутов:
    Если аутентификация успешна:
        request.is_authenticated = True;
        request.user = <server.models.User object ...>;
    Если токен не предоставлен:
        request.is_authenticated = False;
    Если предоставлен невалидный токен возвращается 401 HTTP-ответ.
    """
    request.is_authenticated = False
    if request.authorization and request.authorization.token:
        user_info: dict = _decode_token(request.authorization.token)
        user: User = request.session.get(User, user_info["id"])
        request.user = user
        request.is_authenticated = True
    return request


def authentication(is_auth: bool, is_owner: bool = False):
    """Функция-декоратор назначения прав для выполнения декорируемого метода.

    :is_auth: пользователь должен быть аутентифицирован (предоставить валидный токен);
    :is_owner: пользователь должен являться владельцем запрашиваемого ресурса.

    В зависимости от выбранных опций, при их невыполнении возвращаются 401 или 403 HTTP-ответ.
    """

    def decorator(old_method):
        handlers = {
            "User": _check_permissions_for_user,
            "Advertisement": _check_permissions_for_advertisement,
        }

        @functools.wraps(old_method)
        def new_method(view_class, *args, **kwargs):
            if any([is_auth, is_owner]):
                handlers[view_class.model.__tablename__](is_owner, kwargs)
            response = old_method(view_class, *args, **kwargs)
            return response

        return new_method

    return decorator
