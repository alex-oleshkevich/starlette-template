from pydantic import BaseModel, ConfigDict


class ProfileSerializer(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    photo: str
    language: str
    timezone: str
    color_hash: str

    model_config = ConfigDict(from_attributes=True)
