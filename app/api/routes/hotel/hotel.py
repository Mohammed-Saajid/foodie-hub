import logging

from fastapi import APIRouter, Body, Depends

from app.api.dependencies import get_hotel_service, require_roles_and_terms
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.schemas.hotel.hotel import HotelCreateRequest, HotelRead
from app.services.hotels.service import HotelService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hotels")


@router.post("/create", response_model=HotelRead)
async def create_hotel(
    payload: HotelCreateRequest,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    hotel_service: HotelService = Depends(get_hotel_service),
) -> HotelRead:
    hotel = await hotel_service.create_hotel(
        name=payload.name, manager_id=current_user.id, description=payload.description
    )
    logger.info(f"Hotel created with ID {hotel.id} by user {current_user.id}")
    return HotelRead(
        id=hotel.id,
        name=hotel.name,
        manager_id=getattr(hotel, "manager_id", current_user.id),
        description=hotel.description,
        is_open=hotel.is_open,
    )


@router.patch("/status", response_model=MessageResponse)
async def set_hotel_open_status(
    is_open: bool = Body(..., description="Whether the hotel should be open or closed", embed=True),
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    hotel_service: HotelService = Depends(get_hotel_service),
) -> MessageResponse:
    await hotel_service.set_hotel_open_status(manager_id=current_user.id, is_open=is_open)
    logger.info(
        f"Hotel open status updated by user {current_user.id}."
        "New status: {'open' if is_open else 'closed'}"
    )
    return MessageResponse(message="Hotel status updated successfully")
