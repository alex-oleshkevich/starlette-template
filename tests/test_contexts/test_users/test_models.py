import datetime

from app.contexts.users.models import User


class TestUser:
    def test_is_authenticated(self) -> None:
        user = User()
        assert user.is_authenticated is True

    def test_identity(self) -> None:
        user = User(id=1)
        assert user.identity == "1"

    def test_is_active(self) -> None:
        user = User()
        assert user.is_active is True

        disabled_user = User(disabled_at=datetime.datetime.now(datetime.UTC))
        assert disabled_user.is_active is False

    def test_is_deleted(self) -> None:
        user = User()
        assert user.is_deleted is False

        deleted_user = User(deleted_at=datetime.datetime.now(datetime.UTC))
        assert deleted_user.is_deleted is True

    def test_is_confirmed(self) -> None:
        user = User()
        assert user.is_confirmed is False

        confirmed_user = User(email_confirmed_at=datetime.datetime.now(datetime.UTC))
        assert confirmed_user.is_confirmed is True

    def test_display_name(self) -> None:
        user = User(first_name="John", last_name="Doe")
        assert user.display_name == "John Doe"

        user = User(first_name="John")
        assert user.display_name == "John"

        user = User(last_name="Doe")
        assert user.display_name == "Doe"

        user = User(email="root@localhost")
        assert user.display_name == "root@localhost"

    def test_color_hash(self) -> None:
        user = User(first_name="John", last_name="Doe")
        assert user.color_hash == "#ac5378"

    def test_initials(self) -> None:
        user = User(first_name="John", last_name="Doe")
        assert user.initials == "JD"

        user = User(first_name="John")
        assert user.initials == "J"

        user = User(last_name="Doe")
        assert user.initials == "D"

        user = User(email="root@localhost")
        assert user.initials == "R"

    def test_deactivate(self) -> None:
        user = User()
        user.deactivate()
        assert user.deleted_at is not None
        assert user.email == f"{ user.id }@deleted.tld"

    def test_get_password_hash(self) -> None:
        user = User(password="password")
        assert user.get_password_hash() == "password"

    def test_get_preferred_language(self) -> None:
        user = User(language="en")
        assert user.get_preferred_language() == "en"

    def test_get_timezone(self) -> None:
        user = User(timezone="UTC")
        assert user.get_timezone() == "UTC"

    def test_str(self) -> None:
        user = User(first_name="John", last_name="Doe")
        assert str(user) == "John Doe"

    def test_eq(self) -> None:
        user1 = User(id=1)
        user2 = User(id=1)
        assert user1 == user2

        user3 = User(id=2)
        assert user1 != user3
