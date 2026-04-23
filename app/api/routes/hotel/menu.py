import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_menu_service, require_roles_and_terms
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.schemas.hotel.menu import MenuItemCreateRequest, MenuItemRead, MenuItemUpdateRequest
from app.services.menu.service import MenuService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menu")


@router.get("/{item_id}", response_model=MenuItemRead)
async def get_menu_item(
    item_id: int,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemRead:
    menu_item = await menu_service.get_menu_item(item_id=item_id)

    logger.info(f"Menu item retrieved for hotel manager {current_user.id}. Item id: {item_id}")
    return MenuItemRead(
        id=menu_item.id,
        hotel_id=menu_item.hotel_id,
        name=menu_item.name,
        description=menu_item.description,
        price=float(menu_item.price),
        is_available=menu_item.is_available,
    )


@router.post("/create", response_model=MenuItemRead)
async def create_menu_item(
    payload: MenuItemCreateRequest,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemRead:
    menu_item = await menu_service.create_menu_item(
        hotel_manager_id=current_user.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        is_available=payload.is_available,
    )

    logger.info(f"Menu item created for hotel manager {current_user.id}. Item name: {payload.name}")
    return MenuItemRead(
        id=menu_item.id,
        hotel_id=menu_item.hotel_id,
        name=menu_item.name,
        description=menu_item.description,
        price=float(menu_item.price),
        is_available=menu_item.is_available,
    )


@router.patch("/update/{item_id}", response_model=MenuItemRead)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdateRequest,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemRead:
    menu_item = await menu_service.update_menu_item(
        hotel_manager_id=current_user.id,
        item_id=item_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        is_available=payload.is_available,
    )

    logger.info(
        f"Menu item updated for hotel manager {current_user.id}. Item id: {item_id},"
        "Updates: {payload.model_dump(exclude_none=True)}"
    )
    return MenuItemRead(
        id=menu_item.id,
        hotel_id=menu_item.hotel_id,
        name=menu_item.name,
        description=menu_item.description,
        price=float(menu_item.price),
        is_available=menu_item.is_available,
    )


@router.delete("/delete/{item_id}", response_model=MessageResponse)
async def delete_menu_item(
    item_id: int,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    menu_service: MenuService = Depends(get_menu_service),
) -> MessageResponse:
    await menu_service.delete_menu_item(hotel_manager_id=current_user.id, item_id=item_id)

    logger.info(f"Menu item deleted for hotel manager {current_user.id}. Item id: {item_id}")
    return MessageResponse(message=f"Menu item {item_id} deleted")
