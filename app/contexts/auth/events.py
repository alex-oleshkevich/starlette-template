from app.contrib.events import Event


class UserAuthenticated(Event):
    user_id: int
