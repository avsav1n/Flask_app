import re

from server.models import User
from tests.utils import FlaskClient


def url(id: int = None):
    base_url = "/user"
    if not id:
        return base_url
    return f"{base_url}/{id}"


def test_get_list_success(user_factory, client: FlaskClient):
    users: list = user_factory(2)

    response = client.get(url())

    assert response.status_code == 200
    assert isinstance(response.json, list)
    for user in users:
        assert user.as_dict in response.json


def test_get_detail_success(client: FlaskClient):
    response = client.get(url(client.user_dict["id"]))

    assert response.status_code == 200
    assert client.user_dict == response.json


def test_post_success(user_factory, client: FlaskClient):
    user_data: dict = user_factory(raw=True)

    response = client.post(url(), json=user_data)

    assert response.status_code == 201
    assert user_data["username"] == response.json["username"]


def test_post_fail_simple_password(user_factory, client: FlaskClient):
    user_data: dict = user_factory(raw=True, password="simple password")
    response = client.post(url(), json=user_data)

    assert response.status_code == 400
    assert response.json.get("error", None)


def test_post_fail_no_name(user_factory, client: FlaskClient):
    user_data: dict = user_factory(raw=True)
    user_data.pop("username")

    response = client.post(url(), json=user_data)

    assert response.status_code == 400
    assert response.json.get("error", None)


def test_post_fail_existed_name(user_factory, client: FlaskClient):
    user_data: dict = user_factory(raw=True, username=client.user_dict["username"])

    response = client.post(url(), json=user_data)

    assert response.status_code == 409
    assert response.json.get("error", None)


def test_patch_fail_unauthorized(client: FlaskClient):
    response = client.patch(url(client.user_dict["id"]), json={"password": "QWErty123"})

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_patch_authorized_owner_success(client: FlaskClient):
    response = client.patch(
        url(client.user_dict["id"]), json={"password": "QWErty123"}, auth=client.token
    )

    assert response.status_code == 200
    assert client.user_dict == response.json


def test_patch_authorized_fail_not_owner(user_factory, client: FlaskClient):
    user: User = user_factory()

    response = client.patch(url(user.id), json={"password": "QWErty123"}, auth=client.token)

    assert response.status_code == 403
    assert response.json.get("error", None)


def test_delete_fail_unauthorized(user_factory, client: FlaskClient):
    user: User = user_factory()

    response = client.delete(url(user.id))

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_delete_authorized_fail_not_owner(user_factory, client: FlaskClient):
    user: User = user_factory()

    response = client.delete(url(user.id), auth=client.token)

    assert response.status_code == 403
    assert response.json.get("error", None)


def test_login_success(user_factory, client: FlaskClient):
    user_data: dict = user_factory(raw=True)
    user_factory(**client.bcrypt.hash_password(user_data.copy()))

    response = client.post("/login", auth=tuple(user_data.values()))

    assert response.status_code == 201
    assert re.fullmatch(
        pattern=r"^[A-Za-z0-9_-]{2,}(?:\.[A-Za-z0-9_-]{2,}){2}$", string=response.json["auth_token"]
    )


def test_fail_invalid_token(client: FlaskClient):
    response = client.get(url(), auth=client.invalid_token)

    assert response.status_code == 401
    assert response.json.get("error", None)
