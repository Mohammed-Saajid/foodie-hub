from fastapi import APIRouter

# Import submodules to register their routes
from app.api.routes.consumer.hotels import router as hotels_router
from app.api.routes.consumer.orders import router as orders_router
from app.api.routes.consumer.user import router as user_router


router = APIRouter(prefix="/consumer", tags=["Consumer"])

# Include sub-routers for different consumer functionalities
router.include_router(hotels_router)
router.include_router(orders_router)
router.include_router(user_router)
