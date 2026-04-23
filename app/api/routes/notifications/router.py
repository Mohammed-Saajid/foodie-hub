from fastapi import APIRouter

from app.api.routes.notifications.sse import router as notifications_router


router = APIRouter(prefix="/notifications", tags=["Notifications"])
router.include_router(notifications_router)
