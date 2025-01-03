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


class ResetPasswordValidator(BaseModel):
    email: str


class ResetPasswordSerializer(BaseModel):
    pass


class ChangePasswordValidator(BaseModel):
    email: str
    signature: str
    password: str
    password_confirm: str


class ChangePasswordSerializer(BaseModel):
    pass
