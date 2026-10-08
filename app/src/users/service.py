from .model import User
from .utils import hash_password


async def create_user(user_data: dict) -> User:
    """Create a new user with hashed password."""
    user_data['password'] = hash_password(user_data['password'])
    user = User(**user_data)
    await user.insert()
    return user


async def get_user_by_email(email: str) -> User | None:
    """Retrieve a user by email."""
    user = await User.find_one(User.email == email)
    return user


async def list_users() -> list[User]:
    """List all users."""
    users = await User.find_all().to_list()
    return users
