import factory
from flask.testing import FlaskClient
from werkzeug.datastructures import Authorization

from server.models import Advertisement, Session, User
from server.permissions import encode_token
from server.routes import app
from server.security import AppBcrypt


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    username: str = factory.Faker("hostname")
    password: str = factory.Faker("password")

    class Meta:
        model = User
        sqlalchemy_session_factory = Session
        sqlalchemy_session_persistence = "commit"


class AdvertisementFactory(factory.alchemy.SQLAlchemyModelFactory):
    title: str = factory.Faker("sentence")
    text: str = factory.Faker("paragraph", nb_sentences=10)
    user: User = factory.SubFactory(UserFactory)

    class Meta:
        model = Advertisement
        sqlalchemy_session_factory = Session
        sqlalchemy_session_persistence = "commit"


class TestAPIClient(FlaskClient):

    def __init__(self, *args, **kwargs):
        self.bcrypt = AppBcrypt(app=app)
        self._user_data: dict = UserFactory.stub().__dict__
        self.user: User = UserFactory.create(**self.bcrypt.hash_password(self._user_data.copy()))

        self.user_dict: dict = self.user.as_dict

        self.invalid_token: Authorization = Authorization(auth_type="token", token="invalid-token")
        self.token: Authorization = Authorization(
            auth_type="token",
            token=encode_token(self.user)["auth_token"],
        )
        super().__init__(*args, **kwargs)
