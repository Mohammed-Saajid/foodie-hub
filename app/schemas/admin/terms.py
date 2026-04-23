from pydantic import BaseModel, Field


class TermsAndConditionsResponse(BaseModel):
    version: int = Field(..., description="The version number of the terms and conditions.")
    content: str = Field(..., description="The full text of the terms and conditions.")
