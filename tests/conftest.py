import pytest

from server.models import Session
from server.routes import app
from tests.utils import AdvertisementFactory, TestAPIClient, UserFactory


@pytest.fixture(scope="function", autouse=True)
def session():
    session = Session()
    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="session", autouse=True)
def flask_app():
    app.testing = True
    yield app


@pytest.fixture(scope="session")
def client() -> TestAPIClient:
    return TestAPIClient(app)


@pytest.fixture(scope="module")
def user_factory():
    def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return UserFactory.stub(**kwargs).__dict__
        if size:
            return UserFactory.create_batch(size, **kwargs)
        return UserFactory.create(**kwargs)

    return factory


@pytest.fixture(scope="module")
def adv_factory():
    def factory(size: int = None, /, **kwargs):
        if kwargs.pop("raw", None):
            return AdvertisementFactory.stub(**kwargs).__dict__
        if size:
            return AdvertisementFactory.create_batch(size, **kwargs)
        return AdvertisementFactory.create(**kwargs)

    return factory
