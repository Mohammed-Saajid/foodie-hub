import logging

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_terms_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.admin.terms import TermsAndConditionsResponse
from app.schemas.auth.auth import CurrentUser, MessageResponse
from app.services.terms.service import TermsService


router = APIRouter(prefix="/terms")
logger = logging.getLogger(__name__)


@router.patch("/terms-and-conditions", response_model=MessageResponse)
async def update_terms_and_conditions(
    content: str = Query(
        ...,
        description="The full text of the new terms and conditions.",
        examples=["No one has enemies,..."],
    ),
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    terms_service: TermsService = Depends(get_terms_service),
) -> MessageResponse:
    """
    Update terms and conditions. Only admins can perform this action.

    This endpoint deactivates the current active T&C and creates a new version.
    Users will need to accept the new terms on their next login.
    """

    version = await terms_service.update_terms_and_conditions(content)
    logger.info(f"Admin {user.id} updated terms and conditions to version {version}")

    return MessageResponse(
        message=f"Terms and conditions updated to version {version}."
        "Users will need to accept the new terms."
    )


@router.get("/terms-and-conditions", response_model=TermsAndConditionsResponse)
async def get_active_terms_and_conditions(
    user: CurrentUser = Depends(
        require_roles_and_terms(
            UserRole.ADMIN, UserRole.CONSUMER, UserRole.DELIVERY, UserRole.HOTEL_MANAGER
        )
    ),
    terms_service: TermsService = Depends(get_terms_service),
) -> TermsAndConditionsResponse:
    """
    Get the currently active terms and conditions. Only admins can access this endpoint.
    """
    active_terms = await terms_service.get_terms_and_conditions()

    logger.info(
        f"User {user.id} retrieved active terms and conditions version {active_terms.version}"
    )
    return TermsAndConditionsResponse(
        version=active_terms.version,
        content=active_terms.content,
    )
