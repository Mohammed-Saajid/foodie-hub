from fastapi import APIRouter

from app.api.routes.admin.router import router as admin_router
from app.api.routes.auth.router import router as auth_router
from app.api.routes.consumer.router import router as consumer_router
from app.api.routes.delivery.router import router as delivery_router
from app.api.routes.hotel.router import router as hotel_manager_router
from app.api.routes.notifications.router import router as notifications_router
from app.api.routes.support.router import router as support_router
from app.api.routes.welcome import router as welcome_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(consumer_router)
api_router.include_router(delivery_router)
api_router.include_router(hotel_manager_router)
api_router.include_router(admin_router)
api_router.include_router(support_router)
api_router.include_router(welcome_router)
api_router.include_router(notifications_router)
