from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from typing import Annotated

from .auth import authenticate_user
from .utils import create_access_token, create_refresh_token, decode_refresh_token


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


form_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(form: form_dependency, response: Response):
    """Authenticate a user and return an access token."""
    user = await authenticate_user(form.username, form.password)
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict"
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/refresh")
async def refresh_token(request: Request):
    """Refresh the access token using the refresh token from cookies."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not found in cookies."
        )
    try:
        payload = decode_refresh_token(refresh_token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token."
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token."
        )

    access_token = create_access_token(data={"sub": email})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(response: Response):
    """Logout the user by clearing the refresh token cookie."""
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully."}
