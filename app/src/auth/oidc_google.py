from fastapi import Request, HTTPException, status
from authlib.integrations.starlette_client import OAuth

from ..users import service
from ..config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

import uuid


oauth = OAuth()


oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)


async def authenticate_via_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google auth failed")
    email = user_info.get("email")
    user_exists = await service.get_user_by_email(email)

    if not user_exists:
        await service.create_user({"email": email, "password": uuid.uuid4().hex})

    return email
