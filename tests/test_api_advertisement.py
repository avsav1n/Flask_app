from server.models import Advertisement
from tests.utils import FlaskClient


def url(id: int = None):
    base_url = "/advertisement"
    if not id:
        return base_url
    return f"{base_url}/{id}"


def test_get_list_success(adv_factory, client: FlaskClient):
    advs: list = adv_factory(2)

    response = client.get(url())

    assert response.status_code == 200
    assert isinstance(response.json, list)
    for adv in advs:
        assert adv.as_dict in response.json


def test_get_detail_success(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory(user=client.user)

    response = client.get(url(adv.id))

    assert response.status_code == 200
    assert adv.as_dict == response.json


def test_post_authorized_success(adv_factory, client: FlaskClient):
    adv_data: dict = adv_factory(raw=True)
    adv_data.pop("user", None)

    response = client.post(url(), json=adv_data, auth=client.token)

    assert response.status_code == 201
    assert adv_data["title"] == response.json["title"]
    assert adv_data["text"] == response.json["text"]
    assert client.user_dict["id"] == response.json["id_user"]


def test_post_fail_existed_title(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory()
    adv_data: dict = adv_factory(raw=True, title=adv.title)
    adv_data.pop("user", None)

    response = client.post(url(), json=adv_data)

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_post_fail_unauthorized(adv_factory, client: FlaskClient):
    adv_data: dict = adv_factory(raw=True)
    adv_data.pop("user", None)

    response = client.post(url(), json=adv_data)

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_post_fail_no_text(adv_factory, client: FlaskClient):
    adv_data: dict = adv_factory(raw=True)
    adv_data.pop("user", None)
    adv_data.pop("text", None)

    response = client.post(url(), json=adv_data)

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_patch_authorized_owner_success(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory(user=client.user)
    text = "Abrakadabra"

    response = client.patch(url(adv.id), json={"text": text}, auth=client.token)

    assert response.status_code == 200
    assert adv.title == response.json["title"]
    assert text == response.json["text"]
    assert client.user_dict["id"] == response.json["id_user"]


def test_patch_authorized_fail_not_owner(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory()
    text = "Abrakadabra"

    response = client.patch(url(adv.id), json={"text": text}, auth=client.token)

    assert response.status_code == 403
    assert response.json.get("error", None)


def test_patch_fail_unauthorized(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory()
    text = "Abrakadabra"

    response = client.patch(url(adv.id), json={"text": text})

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_delete_fail_unauthorized(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory()

    response = client.delete(url(adv.id))

    assert response.status_code == 401
    assert response.json.get("error", None)


def test_delete_authorized_fail_not_owner(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory()

    response = client.delete(url(adv.id), auth=client.token)

    assert response.status_code == 403
    assert response.json.get("error", None)


def test_delete_authorized_success(adv_factory, client: FlaskClient):
    adv: Advertisement = adv_factory(user=client.user)

    response = client.delete(url(adv.id), auth=client.token)

    assert response.status_code == 204
