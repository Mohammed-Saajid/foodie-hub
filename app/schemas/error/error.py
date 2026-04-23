from pydantic import BaseModel


class ErrorDetail(BaseModel):
    loc: list[str]
    msg: str
    type: str


class ErrorResponse(BaseModel):
    status_code: int
    message: str
    details: list[ErrorDetail] | None = None
    headers: dict[str, str] | None = None
