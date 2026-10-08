import jwt
from datetime import timedelta, datetime, timezone


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=10)
REFRESH_TOKEN_EXPIRE_MINUTES = timedelta(days=5)

ACCESS_TOKEN_SECRET_KEY = "your_access_token_secret_key"
REFRESH_TOKEN_SECRET_KEY = "your_refresh_token_secret_key"


def create_token(data: dict, secret_key: str, algorithm: str, expires_delta: timedelta):
    """Create a JWT token."""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_token(token: str, secret_key: str, algorithms: list[str]):
    """Decode a JWT token."""
    try:
        decoded_jwt = jwt.decode(token, secret_key, algorithms=algorithms)
        return decoded_jwt
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token.")


def create_access_token(data: dict):
    """Create an access token."""
    return create_token(data, ACCESS_TOKEN_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)


def decode_access_token(token: str):
    """Decode an access token."""
    return decode_token(token, ACCESS_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])


def create_refresh_token(data: dict):
    """Create a refresh token."""
    return create_token(data, REFRESH_TOKEN_SECRET_KEY, ALGORITHM, REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_refresh_token(token: str):
    """Decode a refresh token."""
    return decode_token(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
