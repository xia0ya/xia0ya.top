"""用户服务"""
from web.models.user import User, authenticate, get_user_by_username, init_users_table

class UserService:
    @staticmethod
    def login(username: str, password: str) -> User | None:
        return authenticate(username, password)

    @staticmethod
    def get_user(username: str) -> User | None:
        return get_user_by_username(username)

    @staticmethod
    def init():
        init_users_table()