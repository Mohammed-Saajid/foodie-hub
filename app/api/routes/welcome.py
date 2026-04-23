from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.auth.auth import MessageResponse, UserRead


router = APIRouter()


@router.get("/welcome", response_model=MessageResponse)
async def welcome(
    current_user: UserRead = Depends(require_roles_and_terms(UserRole.CONSUMER)),
) -> MessageResponse:
    return MessageResponse(message=f"Welcome {current_user.full_name}")
