from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr
from typing import Annotated


class UserBase(BaseModel):
    email: EmailStr
    password: str
    age: int
    skills: list[str] = []
    role: str


class UserResponse(BaseModel):
    email: EmailStr
    age: int
    skills: list[str]
    role: str
    isActive: bool

    class Config:
        orm_mode = True


class User(Document):
    email: Annotated[str, Indexed(unique=True)]
    password: str
    age: int
    isActive: bool = True
    skills: list[str] = []
    role: str

    class Settings:
        name = "users"
        indexes = [
            "email",
            "isActive",
            "role"
        ]
