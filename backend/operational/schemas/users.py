from pydantic import BaseModel

class UserSignUpSchema(BaseModel):
    username: str
    password: str
    email: str
    name: str
    lastname: str

class UserWithoutPasswordSchema(BaseModel):
    username: str
    email: str
    name: str
    lastname: str
    role: str