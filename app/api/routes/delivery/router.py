from fastapi import APIRouter

# Import submodules to register their routes
from app.api.routes.delivery.orders import router as delivery_router


router = APIRouter(prefix="/delivery", tags=["Delivery"])

# Include sub-routers for different delivery functionalities

router.include_router(delivery_router)
