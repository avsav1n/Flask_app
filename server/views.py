import sqlalchemy as sq
from flask import Flask, Response, jsonify, request
from flask.views import MethodView

from server.config import SECRET_KEY
from server.exceptions import HttpError
from server.models import Advertisement, Session, User
from server.permissions import authentication, check_authentication, encode_token
from server.schema import (
    CreateAdvertisement,
    CreateUser,
    UpdateAdvertisement,
    UpdateUser,
    validate,
)
from server.security import AppBcrypt

app = Flask(__name__)
app.secret_key = SECRET_KEY
bcrypt = AppBcrypt(app=app)


@app.before_request
def before_request():
    request.session = Session()
    check_authentication(request)


@app.after_request
def after_request(response: Response):
    request.session.close()
    return response


@app.errorhandler(HttpError)
def error_handler(error: HttpError):
    error_response = jsonify({"error": error.message})
    error_response.status_code = error.status_code
    return error_response


class BaseView(MethodView):
    model = None

    def __init__(self):
        if self.model is None:
            raise TypeError(
                f"{self.__class__.__name__}'s subclasses must override class attribute 'model'"
            )
        super().__init__()

    def commit_changes(self, obj: User | Advertisement = None) -> None:
        """Метод фиксации состояния базы данных."""
        if obj:
            request.session.add(obj)
        try:
            request.session.commit()
        except sq.exc.IntegrityError:
            raise HttpError(409, f"{self.model.__tablename__}-model object already exists")

    def get_obj(self, id: int) -> User | Advertisement:
        """Метод получения объекта модели по идентификатору."""
        obj: User | Advertisement = request.session.get(self.model, id)
        if obj is None:
            raise HttpError(404, f"{self.model.__tablename__}-model object with {id=} not found")
        return obj

    def get_response(self, value: dict | list[dict], status_code: int = 200) -> Response:
        """Метод подготовки ответа с подстановкой кода HTTP-ответа."""
        response: Response = jsonify(value)
        response.status_code = status_code
        return response

    def _get_list_logic(self) -> list[dict]:
        objs: list[User | Advertisement] = request.session.scalars(sq.select(self.model))
        return [obj.as_dict for obj in objs]

    def _get_detail_logic(self, id: int) -> dict:
        obj: User | Advertisement = self.get_obj(id)
        return obj.as_dict

    def get(self, id: int = None) -> Response:
        """Метод обработки HTTP-метода GET.
        Возвращает пользователю список всех или конкретную запись
        из базы данных на основе переданных аргументов.
        """
        objs: dict | list[dict] = self._get_detail_logic(id) if id else self._get_list_logic()
        return self.get_response(objs)

    def delete(self, id: int) -> Response:
        """Метод обработки HTTP-метода DELETE.
        Удаляет запись из базы данных на основе ее идентификатора.
        """
        obj: User | Advertisement = self.get_obj(id)
        request.session.delete(obj)
        self.commit_changes()
        return self.get_response(obj.as_dict, 204)


class UserView(BaseView):
    """View-class для работы с таблицей 'User'."""

    model = User

    @authentication(is_auth=False)
    def get(self, id: int = None) -> Response:
        if id and request.is_authenticated and request.user.id == id:
            return request.user
        return super().get(id)

    @authentication(is_auth=False)
    def post(self) -> Response:
        """Метод обработки HTTP-метода POST.
        Создает новую запись в базе данных о пользователе.
        """
        validated_data: dict = validate(CreateUser, request.json)
        bcrypt.hash_password(validated_data)
        user: User = User(**validated_data)
        self.commit_changes(user)
        return self.get_response(user.as_dict, 201)

    @authentication(is_auth=True, is_owner=True)
    def patch(self, id: int) -> Response:
        """Метод обработки HTTP-метода PATCH.
        Частично меняет информацию о существующем пользователе в базе данных.
        """
        validated_data: dict = validate(UpdateUser, request.json)
        bcrypt.hash_password(validated_data)
        user: User = self.get_obj(id)
        for field, value in validated_data.items():
            setattr(user, field, value)
        self.commit_changes(user)
        return self.get_response(user.as_dict)

    @authentication(is_auth=True, is_owner=True)
    def delete(self, id: int) -> Response:
        return super().delete(id)


class AdvertisementView(BaseView):
    """View-class для работы с таблицей 'Advertisement'."""

    model = Advertisement

    @authentication(is_auth=False)
    def get(self, id: int = None) -> Response:
        return super().get(id)

    @authentication(is_auth=True)
    def post(self) -> Response:
        """Метод обработки HTTP-метода POST.
        Создает новую запись в базе данных об объявлении.
        """
        validated_data: dict = validate(CreateAdvertisement, request.json)
        advertisement: Advertisement = Advertisement(**validated_data, user=request.user)
        self.commit_changes(advertisement)
        return self.get_response(advertisement.as_dict, 201)

    @authentication(is_auth=True, is_owner=True)
    def patch(self, id: int) -> Response:
        """Метод обработки HTTP-метода PATCH.
        Частично меняет информацию о существующем объявлении в базе данных.
        """
        validated_data: dict = validate(UpdateAdvertisement, request.json)
        for adv in request.user.advertisements:
            if adv.id == id:
                advertisement: Advertisement = adv
                break
        for field, value in validated_data.items():
            setattr(advertisement, field, value)
        self.commit_changes(advertisement)
        return self.get_response(advertisement.as_dict)

    @authentication(is_auth=True, is_owner=True)
    def delete(self, id: int) -> Response:
        return super().delete(id)


@app.route("/login", methods=["POST", "PATCH"])
def login() -> Response:
    """View-функция авторизации.

    Возвращает токен для последующей авторизации при выполнении запросов.
    """
    auth = request.authorization
    if auth and "username" in auth.parameters and "password" in auth.parameters:
        query = sq.select(User).where(User.username == auth.parameters["username"])
        user: User = request.session.scalar(query)
        if bcrypt.check_password_hash(user.password, auth.parameters["password"]):
            auth_token = encode_token(user)
        return jsonify(auth_token), 201
    raise HttpError(401, "Basic authorization credentials were not provided")
