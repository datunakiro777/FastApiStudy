from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=20)
    last_name: str = Field(min_length=2, max_length=20)
    age: int = Field(gt=0, lt=100)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    created_at: datetime


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    content: str = Field(min_length=1)


class PostCreate(PostBase):
    user_id: int


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int
    author: UserResponse
    

    
