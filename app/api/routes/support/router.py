from fastapi import APIRouter

# Import submodules to register their routes
from app.api.routes.support.feedback import router as feedback_router
from app.api.routes.support.report import router as report_router


router = APIRouter(prefix="/support", tags=["Support"])

# Include sub-routers for different consumer functionalities
router.include_router(feedback_router)
router.include_router(report_router)
