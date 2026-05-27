from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    tenant_name: str = Field(min_length=1, max_length=120)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    tenant_id: int
    subscription_status: str


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=4000)


class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    summary: str | None

    model_config = {"from_attributes": True}


class SummarizeResponse(BaseModel):
    id: int
    summary: str


class CheckoutResponse(BaseModel):
    checkout_url: str
