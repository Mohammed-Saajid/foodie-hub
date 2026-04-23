from fastapi import APIRouter

# Import submodules to register their routes
from app.api.routes.auth.auth import router as auth_router


router = APIRouter(prefix="/auth", tags=["Auth"])

# Include sub-routers for different consumer functionalities
router.include_router(auth_router)
