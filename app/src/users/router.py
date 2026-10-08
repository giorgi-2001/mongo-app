from fastapi import APIRouter, status, HTTPException

from .model import UserBase, UserResponse
from ..users import service
from ..auth.auth import user_dependency


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserBase):
    """Register a new user."""
    user_exists = await service.get_user_by_email(user.email)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists."
        )
    await service.create_user(user.model_dump())
    return {"message": "User registered successfully."}


@router.get("/", response_model=list[UserResponse])
async def list_users():
    """List all users."""
    users = await service.list_users()
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: user_dependency):
    """Get the current authenticated user's information."""
    return user
