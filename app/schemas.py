from pydantic import BaseModel


# Password Login schema (Pydantic Model)
class LoginPassword(BaseModel):
    email: str
    password: str
    device_id: str


# Pin Login schema (Pydantic Model)
class LoginPin(BaseModel):
    email: str
    pin: str
    device_id: str


# Set Pin schema (Pydantic Model)
class SetPin(BaseModel):
    pin: str


# Full User schema (Pydantic Model)
class User(BaseModel):
    id: int
    zitadel_id: str
    email: str
    device_id: str
    token: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    is_pin_allowed: bool


class TokenData(BaseModel):
    email: str | None = None
