from pydantic import BaseModel, EmailStr


class LoginValidator(BaseModel):
    email: EmailStr
    password: str


class LoginSerializer(BaseModel):
    access_token: str
    refresh_token: str


class LogoutValidator(BaseModel):
    refresh_token: str


class LogoutSerializer(BaseModel): ...


class RefreshTokenValidator(BaseModel):
    refresh_token: str


class RefreshTokenSerializer(BaseModel):
    access_token: str
    refresh_token: str
