from fastapi import APIRouter

from app.api.routes.admin.feedbacks import router as feedback_router

# Import submodules to register their routes
from app.api.routes.admin.orders import router as orders_router
from app.api.routes.admin.reports import router as reports_router
from app.api.routes.admin.terms_and_conditions import router as terms_router
from app.api.routes.admin.user import router as user_router


router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers for different admin functionalities
router.include_router(orders_router)
router.include_router(feedback_router)
router.include_router(reports_router)
router.include_router(terms_router)
router.include_router(user_router)
