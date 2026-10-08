from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from ..users import service as user_service
from ..users.utils import verify_password
from .utils import decode_access_token
from ..logger import logger

from typing import Annotated


TOKEN_URL = "api/v1/auth/login"
REFRESH_URL = "api/v1/auth/refresh"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL, refreshUrl=REFRESH_URL)
token_dependency = Annotated[str, Depends(oauth2_scheme)]


UNAUTHORIZED_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    user = await user_service.get_user_by_email(email)
    if not user:
        raise UNAUTHORIZED_ERROR
    if not verify_password(password, user.password):
        raise UNAUTHORIZED_ERROR
    return user


async def get_current_user(token: str):
    """Get the current user from the JWT token."""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise UNAUTHORIZED_ERROR
    except ValueError as e:
        logger.error(f"Error occurred while decoding token: {e}")
        raise UNAUTHORIZED_ERROR

    user = await user_service.get_user_by_email(email)
    if user is None:
        raise UNAUTHORIZED_ERROR
    return user


async def get_current_active_user(token: token_dependency):
    """Get the current active user from the JWT token."""
    user = await get_current_user(token)
    if not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


user_dependency = Annotated[str, Depends(get_current_active_user)]
