import logging

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_hotel_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.auth.auth import CurrentUser
from app.schemas.consumer.hotel import HotelListResponse, HotelRead
from app.services.hotels.service import HotelService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hotels")


@router.get("", response_model=HotelListResponse)
async def list_hotels(
    current_user: CurrentUser = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.ADMIN, UserRole.DELIVERY, UserRole.HOTEL_MANAGER
        )
    ),
    hotel_service: HotelService = Depends(get_hotel_service),
    limit: int = Query(100, ge=1, le=1000, description="Number of hotels to return"),
    offset: int = Query(0, ge=0, description="Number of hotels to skip"),
    is_open: bool | None = Query(None, description="Filter by open status"),
) -> HotelListResponse:
    hotels, total = await hotel_service.list_hotels(limit=limit, offset=offset, is_open=is_open)
    logger.info(
        f"Consumer {current_user.id} retrieved"
        "list of hotels with limit {limit} and offset {offset}"
    )
    return HotelListResponse(
        hotels=[HotelRead.model_validate(hotel) for hotel in hotels], total=total
    )


@router.get("/{hotel_id}", response_model=HotelRead)
async def get_hotel_details(
    hotel_id: int = Path(..., description="ID of the hotel to retrieve"),
    current_user: CurrentUser = Depends(require_roles_and_terms(UserRole.CONSUMER)),
    hotel_service: HotelService = Depends(get_hotel_service),
) -> HotelRead:
    hotel = await hotel_service.get_hotel_by_id(hotel_id)
    logger.info(f"Consumer {current_user.id} retrieved details for hotel {hotel_id}")
    return HotelRead.model_validate(hotel)
