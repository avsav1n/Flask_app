from flask_bcrypt import Bcrypt


class AppBcrypt(Bcrypt):
    def hash_password(self, data: dict, **kwargs) -> dict:
        """Функция хэширования пароля."""
        if "password" in data:
            hashed_password: bytes = self.generate_password_hash(data["password"], **kwargs)
            data["password"] = hashed_password.decode()
        return data
