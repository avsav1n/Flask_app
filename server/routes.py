from server.views import AdvertisementView, Flask, UserView, app


def register_url(view_class: UserView | AdvertisementView, name: str, app: Flask = app) -> None:
    """Функция регистрации URL всех стандартных REST API методов,
    описанных в class-based views.
    """
    view_func_list = view_class.as_view(name=f"{name}-list")
    view_func_detail = view_class.as_view(name=f"{name}-detail")
    app.add_url_rule(f"/{name}", view_func=view_func_list, methods=["GET", "POST"])
    app.add_url_rule(
        f"/{name}/<int:id>", view_func=view_func_detail, methods=["GET", "PATCH", "DELETE"]
    )


register_url(AdvertisementView, "advertisement")
register_url(UserView, "user")
