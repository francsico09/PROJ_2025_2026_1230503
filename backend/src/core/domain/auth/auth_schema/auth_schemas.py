import uuid

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    user_name: str
    user_email: str
    user_role: str
