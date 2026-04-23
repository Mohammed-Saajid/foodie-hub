import logging

from fastapi import APIRouter, Body, Depends

from app.api.dependencies import get_user_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.auth.auth import CurrentUser
from app.schemas.consumer.user import FullUserRead, UserProfileUpdateRequest
from app.services.users.service import UserService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="")


@router.get("/profile", response_model=FullUserRead)
async def get_profile(
    current_user: CurrentUser = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.ADMIN, UserRole.DELIVERY, UserRole.HOTEL_MANAGER
        )
    ),
    user_service: UserService = Depends(get_user_service),
) -> FullUserRead:
    """
    Get the profile of the currently authenticated user.
    """
    user = await user_service.get_user_by_id(current_user.id)
    return FullUserRead.model_validate(user)


@router.patch("/profile", response_model=FullUserRead)
async def update_profile(
    profile_data: UserProfileUpdateRequest = Body(
        ..., description="Fields to update in the user profile"
    ),
    current_user: CurrentUser = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.ADMIN, UserRole.DELIVERY, UserRole.HOTEL_MANAGER
        )
    ),
    user_service: UserService = Depends(get_user_service),
) -> FullUserRead:

    updated_user = await user_service.update_user_profile(
        user_id=current_user.id,
        name=profile_data.name,
        email=profile_data.email,
        phone_number=profile_data.phone_number,
        about_me=profile_data.about_me,
        profile_picture_url=profile_data.profile_picture_url,
        upi_screenshot_url=profile_data.upi_screenshot_url,
    )
    return FullUserRead.model_validate(updated_user)
