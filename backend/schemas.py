from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=20)
    last_name: str = Field(min_length=2, max_length=20)
    age: int = Field(gt=0, lt=100)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date_created: str
    

    
