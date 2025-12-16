from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"


class UserLogin(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentVersionResponse(BaseModel):
    id: int
    version: int
    original_name: str
    mime_type: Optional[str]
    created_at: datetime
    uploader_id: int

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentBase):
    id: int
    latest_version: int
    created_at: datetime
    updated_at: datetime
    owner_id: Optional[int]
    versions: List[DocumentVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
