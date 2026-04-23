from fastapi import APIRouter

# Import submodules to register their routes
from app.api.routes.hotel.hotel import router as hotel_router
from app.api.routes.hotel.menu import router as menu_order
from app.api.routes.hotel.orders import router as order_router


router = APIRouter(prefix="/hotel-manager", tags=["Hotel Manager"])

# Include sub-routers for different delivery functionalities
router.include_router(hotel_router)
router.include_router(order_router)
router.include_router(menu_order)
